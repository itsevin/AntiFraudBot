from pydantic import BaseModel
# from pydantic import field_validator # 见下面注释

class Config(BaseModel):
    anti_fraud_knowledge_push_group: bool = True
    anti_fraud_knowledge_push_private: bool = False
    anti_fraud_knowledge_push_hour: int = 12
    anti_fraud_knowledge_push_minute: int = 0

    anti_fraud_example_push_group: bool = True
    anti_fraud_example_push_private: bool = False
    anti_fraud_example_push_hour: int = 12
    anti_fraud_example_push_minute: int = 0

    keyword_detection_group: bool = True
    keyword_detection_private: bool = True

    url_detection_group: bool = True
    url_detection_private: bool = True

    alibaba_cloud_acess_key_id: str = None
    alibaba_cloud_acess_key_secret: str = None

    # 这段代码要求 pydantic 大版本号为 2，和阿里云的api库冲突了，所以停用
    # @field_validator("anti_fraud_knowledge_push_hour")
    # @classmethod
    # def check_knowledge_hour(cls, v: int) -> int:
    #     if v >= 0 and v <= 12:
    #         return v
    #     raise ValueError("anti_fraud_knowledge_push_hour 的范围应该在 0-12 之间")
    
    # @field_validator("anti_fraud_knowledge_push_minute")
    # @classmethod
    # def check_knowledge_minute(cls, v: int) -> int:
    #     if v >= 0 and v <= 60:
    #         return v
    #     raise ValueError("anti_fraud_knowledge_push_minute 的范围应该在 0-60 之间")
    
    # @field_validator("anti_fraud_example_push_hour")
    # @classmethod
    # def check_example_hour(cls, v: int) -> int:
    #     if v >= 0 and v <= 12:
    #         return v
    #     raise ValueError("anti_fraud_example_push_hour 的范围应该在 0-12 之间")
    
    # @field_validator("anti_fraud_example_push_minute")
    # @classmethod
    # def check_example_minute(cls, v: int) -> int:
    #     if v >= 0 and v <= 60:
    #         return v
    #     raise ValueError("anti_fraud_example_push_minute 的范围应该在 0-60 之间")
    