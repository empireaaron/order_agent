"""
Milvus 向量数据库连接和索引管理
"""
import logging
from pymilvus import MilvusClient, DataType

from config import settings

logger = logging.getLogger(__name__)


class MilvusManager:
    """Milvus 管理器"""

    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.db_name = settings.MILVUS_DB_NAME
        self.client = None

    def connect(self):
        """连接 Milvus"""
        try:
            self.client = MilvusClient(
                uri=f"http://{self.host}:{self.port}",
                db_name=self.db_name
            )
            return True
        except Exception as e:
            logger.error(f"Milvus connection failed: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.client:
            self.client.close()
            self.client = None

    def create_collection(self, collection_name: str, dimension: int = 384):
        """创建 Collection

        Args:
            collection_name: 集合名称
            dimension: 向量维度 (默认 384 for all-MiniLM-L6-v2)
        """
        if not self.client:
            self.connect()

        try:
            if self.client.has_collection(collection_name):
                logger.info(f"Collection {collection_name} already exists")
                return True

            # 使用显式 schema 定义，支持字符串类型的 ID
            schema = self.client.create_schema(
                auto_id=False,
                enable_dynamic_field=True
            )

            # 添加主键字段 - 使用 VARCHAR 支持字符串 ID
            schema.add_field(
                field_name="id",
                datatype=DataType.VARCHAR,
                is_primary=True,
                max_length=100
            )

            # 添加向量字段
            schema.add_field(
                field_name="vector",
                datatype=DataType.FLOAT_VECTOR,
                dim=dimension
            )

            # 添加元数据字段 (JSON)
            schema.add_field(
                field_name="metadata",
                datatype=DataType.JSON
            )

            # 创建索引
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="IVF_FLAT",
                metric_type="L2",
                params={"nlist": 128}
            )

            # 创建集合
            self.client.create_collection(
                collection_name=collection_name,
                schema=schema,
                index_params=index_params
            )

            logger.info(f"Collection {collection_name} created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False

    def insert(self, collection_name: str, data: list) -> bool:
        """插入数据

        Args:
            collection_name: 集合名称
            data: 插入数据列表
        """
        if not self.client:
            self.connect()

        try:
            # 先检查集合是否存在
            if not self.client.has_collection(collection_name):
                logger.info(f"Collection {collection_name} does not exist, trying to create...")
                # 尝试自动创建集合
                dimension = len(data[0]["vector"]) if data else 1536
                if self.create_collection(collection_name, dimension):
                    logger.info(f"Collection {collection_name} created successfully, continuing data insertion...")
                else:
                    logger.error(f"Failed to auto-create collection {collection_name}")
                    return False

            self.client.insert(
                collection_name=collection_name,
                data=data
            )
            return True
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to insert data: {error_msg}")

            # 检测是否是 schema 类型不匹配错误
            if "should be a int64" in error_msg or "should be a varchar" in error_msg:
                logger.warning(f"\n[Error Hint] Collection {collection_name} schema mismatch with current data type.")
                logger.warning("Possible cause: The collection was created with old code, ID field type is int64, but new code uses varchar.")
                logger.warning("Solution: Delete and recreate the knowledge base, or manually drop the collection in Milvus.")

            return False


    def search(self, collection_name: str, vector: list, limit: int = 5, score_threshold: float = 0.0) -> list:
        """搜索相似向量

        Args:
            collection_name: 集合名称
            vector: 查询向量
            limit: 返回数量
            score_threshold: 相似度分数阈值（0-1之间），低于此值的结果会被过滤

        Returns:
            搜索结果列表，每个结果包含 id, distance, metadata
        """
        if not self.client:
            self.connect()

        try:
            results = self.client.search(
                collection_name=collection_name,
                data=[vector],
                limit=limit,
                output_fields=["metadata"]
            )

            if not results or not results[0]:
                return []

            # 过滤低于阈值的结果
            filtered_results = []
            for result in results[0]:
                # Milvus 返回的距离分数，范围通常是 [0, 2] 或 [-1, 1]，取决于 metric_type
                # 对于 cosine 相似度，需要转换为 [0, 1] 范围
                distance = result.get('distance', 0)

                # 如果是 cosine 相似度，转换为 0-1 范围
                # Milvus 的 cosine 距离 = 1 - cosine_similarity
                # 所以 similarity = 1 - distance
                if distance <= 1.0:  # 假设是 cosine 距离
                    similarity = 1 - distance
                else:  # 可能是 L2 距离，需要归一化
                    similarity = 1 / (1 + distance)

                if similarity >= score_threshold:
                    result['similarity'] = similarity
                    filtered_results.append(result)

            return filtered_results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def delete_by_filter(self, collection_name: str, filter_expr: str) -> bool:
        """根据条件删除数据

        Args:
            collection_name: 集合名称
            filter_expr: 过滤表达式
        """
        if not self.client:
            self.connect()

        try:
            self.client.delete(
                collection_name=collection_name,
                filter=filter_expr
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete data: {e}")
            return False

    def query(self, collection_name: str, filter_expr: str, output_fields: list = None) -> list:
        """查询数据

        Args:
            collection_name: 集合名称
            filter_expr: 过滤表达式
            output_fields: 输出字段列表

        Returns:
            查询结果列表
        """
        if not self.client:
            self.connect()

        try:
            results = self.client.query(
                collection_name=collection_name,
                filter=filter_expr,
                output_fields=output_fields or ["*"]
            )
            return results
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def get_collection_stats(self, collection_name: str) -> dict:
        """获取集合统计信息

        Args:
            collection_name: 集合名称

        Returns:
            统计信息字典
        """
        if not self.client:
            self.connect()

        try:
            row_count = self.client.get_collection_stats(collection_name)["row_count"]
            return {"collection_name": collection_name, "row_count": row_count}
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def drop_collection(self, collection_name: str) -> bool:
        """删除集合

        Args:
            collection_name: 集合名称

        Returns:
            是否成功
        """
        if not self.client:
            self.connect()

        try:
            if self.client.has_collection(collection_name):
                self.client.drop_collection(collection_name)
                logger.info(f"Collection {collection_name} deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False

    def has_collection(self, collection_name: str) -> bool:
        """检查集合是否存在

        Args:
            collection_name: 集合名称

        Returns:
            是否存在
        """
        if not self.client:
            self.connect()

        try:
            return self.client.has_collection(collection_name)
        except Exception as e:
            logger.error(f"Failed to check collection: {e}")
            return False


# 全局 Milvus 管理器实例
milvus_manager = MilvusManager()


def get_milvus_client():
    """获取 Milvus 客户端"""
    if not milvus_manager.client:
        milvus_manager.connect()
    return milvus_manager.client