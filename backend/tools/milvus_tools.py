"""
Milvus 工具函数 - 知识库检索
"""
import logging
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from db.milvus import milvus_manager

logger = logging.getLogger(__name__)


def generate_collection_name() -> str:
    """生成合法的 Milvus collection 名称（只包含数字、字母和下划线）"""
    # 使用 UUID 生成唯一名称，去掉连字符
    unique_id = str(uuid.uuid4()).replace('-', '')
    return f"kb_{unique_id}"


def get_embedding_dimension() -> int:
    """获取当前 embedding 模型的维度"""
    from config import settings
    # DashScope text-embedding-v2: 1536 维
    # OpenAI text-embedding-3-small: 1536 维
    return 1536


def generate_embedding(text: str) -> List[float]:
    """
    使用配置好的 embedding 模型生成文本向量

    Args:
        text: 输入文本

    Returns:
        向量列表
    """
    from config import settings
    from openai import OpenAI

    try:
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )

        return response.data[0].embedding
    except Exception as e:
        logger.error("生成 embedding 失败: %s", e)
        # 失败时返回零向量（会导致搜索无结果，但不会报错）
        return [0.0] * get_embedding_dimension()


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    批量生成文本向量

    Args:
        texts: 输入文本列表

    Returns:
        向量列表
    """
    from config import settings
    from openai import OpenAI

    if not texts:
        return []

    try:
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts
        )

        # 按 index 排序确保顺序一致
        embeddings = sorted(response.data, key=lambda d: d.index)
        return [e.embedding for e in embeddings]
    except Exception as e:
        logger.error("批量生成 embedding 失败: %s", e)
        # 失败时全部返回零向量
        dim = get_embedding_dimension()
        return [[0.0] * dim for _ in texts]


def retrieve_from_knowledge_base(
    question: str,
    collection_name: str,
    top_k: int = 5,
    similarity_threshold: float = 0.0
) -> List[Dict[str, Any]]:
    """
    从知识库检索相关信息

    Args:
        question: 用户问题
        collection_name: Milvus collection 名称
        top_k: 返回_top_k_条结果
        similarity_threshold: 相似度阈值，低于此值的结果会被过滤

    Returns:
        检索结果列表
    """
    # 生成真实的 embedding 向量
    query_vector = generate_embedding(question)
    logger.debug("生成的查询向量维度: %s", len(query_vector))

    results = milvus_manager.search(
        collection_name=collection_name,
        vector=query_vector,
        limit=top_k,
        score_threshold=similarity_threshold
    )

    return results


def create_knowledge_base_collection(kb_name: str) -> tuple[bool, str]:
    """
    创建知识库 collection

    Args:
        kb_name: 知识库名称

    Returns:
        (是否成功, collection_name)
    """
    from config import settings

    collection_name = generate_collection_name()

    # 根据 embedding 模型确定维度
    dimension = get_embedding_dimension()

    success = milvus_manager.create_collection(collection_name=collection_name, dimension=dimension)
    return success, collection_name if success else ""


def insert_document_to_kb(
    collection_name: str,
    chunks: List[str],
    metadata_list: List[Dict]
) -> bool:
    """
    将文档分块插入知识库

    Args:
        collection_name: 集合名称
        chunks: 文本分块列表
        metadata_list: 元数据列表

    Returns:
        是否成功
    """
    # 批量生成 embedding，避免对每个 chunk 单独发起 HTTP 请求
    vectors = generate_embeddings_batch(chunks)

    data = []
    for i, (chunk, metadata, vector) in enumerate(zip(chunks, metadata_list, vectors)):
        data.append({
            "id": f"doc_{i}_{uuid.uuid4().hex[:8]}",
            "vector": vector,
            "metadata": {
                **metadata,
                "content": chunk
            }
        })

    return milvus_manager.insert(collection_name=collection_name, data=data)


def search_kb_with_vector(
    query_vector: List[float],
    collection_name: str,
    top_k: int = 3,
    similarity_threshold: float = 0.6,
    kb_name: str = "unknown"
) -> tuple[str, list]:
    """
    使用预计算的向量在知识库中搜索（避免重复生成 embedding）

    Args:
        query_vector: 查询向量
        collection_name: 集合名称
        top_k: 相关块数量
        similarity_threshold: 相似度阈值
        kb_name: 知识库名称（用于调试）

    Returns:
        (检索到的上下文文本, 原始结果列表)
    """
    results = milvus_manager.search(
        collection_name=collection_name,
        vector=query_vector,
        limit=top_k,
        score_threshold=similarity_threshold
    )

    if not results:
        return "", []

    # 按相似度排序（降序）
    results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)

    # 提取内容，添加相似度信息用于调试
    context_parts = []
    for r in results:
        content = r.get("metadata", {}).get("content", "")
        similarity = r.get('similarity', 0)
        if content:
            context_parts.append(content)
            logger.debug("[%s] 相似度: %.3f: %s...", kb_name, similarity, content[:80])

    # 拼接结果，限制总长度
    MAX_CONTEXT_LENGTH = 2000
    context = "\n\n".join(context_parts)
    if len(context) > MAX_CONTEXT_LENGTH:
        context = context[:MAX_CONTEXT_LENGTH] + "\n...[内容已截断]"

    return context, results


def search_kb(
    question: str,
    collection_name: str,
    top_k: int = 3,
    similarity_threshold: float = 0.6
) -> tuple[str, list]:
    """
    在知识库中搜索答案并返回上下文（兼容旧接口）

    Args:
        question: 用户问题
        collection_name: 集合名称
        top_k: 相关块数量
        similarity_threshold: 相似度阈值，低于此值的结果会被过滤（0-1之间）

    Returns:
        (检索到的上下文文本, 原始结果列表)
    """
    results = retrieve_from_knowledge_base(
        question=question,
        collection_name=collection_name,
        top_k=top_k,
        similarity_threshold=similarity_threshold
    )

    if not results:
        return "", []

    # 按相似度排序（降序）
    results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)

    # 提取内容，添加相似度信息用于调试
    context_parts = []
    for r in results:
        content = r.get("metadata", {}).get("content", "")
        similarity = r.get('similarity', 0)
        if content:
            context_parts.append(content)
            logger.debug("知识库结果 [相似度: %.3f]: %s...", similarity, content[:80])

    # 拼接结果，限制总长度（避免超出 LLM 上下文）
    MAX_CONTEXT_LENGTH = 2000  # 最大上下文长度
    context = "\n\n".join(context_parts)
    if len(context) > MAX_CONTEXT_LENGTH:
        context = context[:MAX_CONTEXT_LENGTH] + "\n...[内容已截断]"

    return context, results


def search_kb_batch(
    query_vector: List[float],
    knowledge_bases: List[Any],
    top_k: int = 3,
    similarity_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    使用预计算向量并行搜索多个知识库

    Args:
        query_vector: 预计算的查询向量
        knowledge_bases: 知识库列表（KnowledgeBase 对象列表）
        top_k: 每个知识库返回的结果数
        similarity_threshold: 相似度阈值

    Returns:
        合并后的搜索结果列表（带 kb_name 标记）
    """
    all_results = []

    def search_single(kb):
        try:
            results = milvus_manager.search(
                collection_name=kb.collection_name,
                vector=query_vector,
                limit=top_k,
                score_threshold=similarity_threshold
            )
            # 添加知识库名称到结果中
            for r in results:
                r['kb_name'] = kb.name
            return results
        except Exception as e:
            logger.error("搜索知识库 %s 失败: %s", kb.name, e)
            return []

    # 并行查询所有知识库
    with ThreadPoolExecutor(max_workers=min(len(knowledge_bases), 10)) as executor:
        future_to_kb = {executor.submit(search_single, kb): kb for kb in knowledge_bases}
        for future in as_completed(future_to_kb):
            results = future.result()
            all_results.extend(results)

    return all_results