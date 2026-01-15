"""
测试文档上传到 Assistant
"""
import os
from dotenv import load_dotenv
from .init_echo import upload_document_to_assistant

load_dotenv()

def test_upload():
    """测试上传文档"""
    assistant_id = os.getenv("BACKBOARD_ASSISTANT_ID")
    
    if not assistant_id:
        print("❌ 未找到 BACKBOARD_ASSISTANT_ID")
        print("   请先运行: python -m backend.init_echo")
        return False
    
    print(f"🔍 当前 Assistant ID: {assistant_id}")
    
    # 上传文档
    doc_path = os.path.join(os.path.dirname(__file__), "docs", "Plan Builder.txt")
    
    if not os.path.exists(doc_path):
        print(f"❌ 文档不存在: {doc_path}")
        return False
    
    print(f"📄 准备上传: {doc_path}")
    
    try:
        document_id = upload_document_to_assistant(doc_path, assistant_id)
        
        if document_id:
            print(f"\n✅ 上传成功!")
            print(f"   Document ID: {document_id}")
            return True
        else:
            print("\n❌ 上传失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False

if __name__ == "__main__":
    test_upload()
