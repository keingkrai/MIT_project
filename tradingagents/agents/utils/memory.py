# import chromadb
# from chromadb.config import Settings
# from openai import OpenAI


# class FinancialSituationMemory:
#     def __init__(self, name, config):
#         if config["backend_url"] == "http://localhost:11434/v1":
#             self.embedding = "nomic-embed-text"
#         else:
#             self.embedding = "text-embedding-3-small"
#         self.client = OpenAI(base_url=config["backend_url"])
#         self.chroma_client = chromadb.Client(Settings(allow_reset=True))
#         self.situation_collection = self.chroma_client.create_collection(name=name)

#     def get_embedding(self, text):
#         """Get OpenAI embedding for a text"""
        
#         response = self.client.embeddings.create(
#             model=self.embedding, input=text
#         )
#         return response.data[0].embedding

#     def add_situations(self, situations_and_advice):
#         """Add financial situations and their corresponding advice. Parameter is a list of tuples (situation, rec)"""

#         situations = []
#         advice = []
#         ids = []
#         embeddings = []

#         offset = self.situation_collection.count()

#         for i, (situation, recommendation) in enumerate(situations_and_advice):
#             situations.append(situation)
#             advice.append(recommendation)
#             ids.append(str(offset + i))
#             embeddings.append(self.get_embedding(situation))

#         self.situation_collection.add(
#             documents=situations,
#             metadatas=[{"recommendation": rec} for rec in advice],
#             embeddings=embeddings,
#             ids=ids,
#         )

#     def get_memories(self, current_situation, n_matches=1):
#         """Find matching recommendations using OpenAI embeddings"""
#         query_embedding = self.get_embedding(current_situation)

#         results = self.situation_collection.query(
#             query_embeddings=[query_embedding],
#             n_results=n_matches,
#             include=["metadatas", "documents", "distances"],
#         )

#         matched_results = []
#         for i in range(len(results["documents"][0])):
#             matched_results.append(
#                 {
#                     "matched_situation": results["documents"][0][i],
#                     "recommendation": results["metadatas"][0][i]["recommendation"],
#                     "similarity_score": 1 - results["distances"][0][i],
#                 }
#             )

#         return matched_results


# if __name__ == "__main__":
#     # Example usage
#     matcher = FinancialSituationMemory()

#     # Example data
#     example_data = [
#         (
#             "High inflation rate with rising interest rates and declining consumer spending",
#             "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
#         ),
#         (
#             "Tech sector showing high volatility with increasing institutional selling pressure",
#             "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
#         ),
#         (
#             "Strong dollar affecting emerging markets with increasing forex volatility",
#             "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
#         ),
#         (
#             "Market showing signs of sector rotation with rising yields",
#             "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
#         ),
#     ]

#     # Add the example situations and recommendations
#     matcher.add_situations(example_data)

#     # Example query
#     current_situation = """
#     Market showing increased volatility in tech sector, with institutional investors 
#     reducing positions and rising interest rates affecting growth stock valuations
#     """

#     try:
#         recommendations = matcher.get_memories(current_situation, n_matches=2)

#         for i, rec in enumerate(recommendations, 1):
#             print(f"\nMatch {i}:")
#             print(f"Similarity Score: {rec['similarity_score']:.2f}")
#             print(f"Matched Situation: {rec['matched_situation']}")
#             print(f"Recommendation: {rec['recommendation']}")

#     except Exception as e:
#         print(f"Error during recommendation: {str(e)}")

import chromadb
from chromadb.config import Settings
# from openai import OpenAI # <--- ไม่ต้องใช้ OpenAI client ที่นี่แล้ว

# --- เพิ่มส่วน Import ใหม่ ---
from sentence_transformers import SentenceTransformer
# -------------------------

class FinancialSituationMemory:
    def __init__(self, name, config):
        
        # --- ส่วนแก้ไขเริ่มต้น ---
        # 1. โหลด Embedding Model แบบ Open Source มาไว้ในหน่วยความจำ
        # 'all-MiniLM-L6-v2' เป็นโมเดลที่เล็ก เร็ว และมีคุณภาพดีมากสำหรับงานทั่วไป
        # ครั้งแรกที่รัน โค้ดจะดาวน์โหลดโมเดลนี้มาเก็บไว้ในเครื่องคุณโดยอัตโนมัติ
        print("Initializing Open Source Embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model initialized.")
        # --- ส่วนแก้ไขสิ้นสุด ---

        # ส่วนของ ChromaDB ยังคงเดิม
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        # self.situation_collection = self.chroma_client.create_collection(name=name)
        self.situation_collection = self.chroma_client.get_or_create_collection(name=name)

    def get_embedding(self, text):
        """Get embedding for a text using a local SentenceTransformer model"""
        
        # --- ส่วนแก้ไข ---
        # ใช้โมเดลที่โหลดมาเพื่อแปลงข้อความเป็น embedding
        # .encode() จะคืนค่าเป็น NumPy array ซึ่ง ChromaDB ใช้งานได้เลย
        embedding = self.embedding_model.encode(text)
        return embedding
        # --- สิ้นสุด ---

    def add_situations(self, situations_and_advice):
        """Add financial situations and their corresponding advice. Parameter is a list of tuples (situation, rec)"""

        situations = []
        advice = []
        ids = []
        embeddings = []

        offset = self.situation_collection.count()

        # สร้าง embeddings ทั้งหมดในครั้งเดียวเพื่อความรวดเร็ว
        all_situations_to_embed = [s[0] for s in situations_and_advice]
        all_embeddings = self.embedding_model.encode(all_situations_to_embed)

        for i, (situation, recommendation) in enumerate(situations_and_advice):
            situations.append(situation)
            advice.append(recommendation)
            ids.append(str(offset + i))
        
        # เพิ่ม embeddings ที่สร้างไว้แล้ว
        embeddings.extend(all_embeddings)

        self.situation_collection.add(
            documents=situations,
            metadatas=[{"recommendation": rec} for rec in advice],
            embeddings=embeddings,
            ids=ids,
        )

    def get_memories(self, current_situation, n_matches=1):
        """Find matching recommendations using embeddings"""
        query_embedding = self.get_embedding(current_situation)

        results = self.situation_collection.query(
            query_embeddings=[query_embedding.tolist()], # ChromaDB บางเวอร์ชันต้องการ list
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )

        matched_results = []
        for i in range(len(results["documents"][0])):
            matched_results.append(
                {
                    "matched_situation": results["documents"][0][i],
                    "recommendation": results["metadatas"][0][i]["recommendation"],
                    "similarity_score": 1 - results["distances"][0][i],
                }
            )

        return matched_results


# ส่วน if __name__ == "__main__": ไม่ต้องแก้ไข
# แต่ตอนรันต้องแก้เล็กน้อย เพราะ __init__ ต้องการ name และ config
if __name__ == "__main__":
    # Example usage
    # สร้าง config จำลองขึ้นมาเพื่อทดสอบ
    mock_config = {"backend_url": ""} # ไม่ได้ใช้แล้ว แต่ใส่ไว้ให้โค้ดรันผ่าน
    matcher = FinancialSituationMemory(name="test_memory", config=mock_config)

    # ... ส่วนที่เหลือทำงานได้เหมือนเดิม ...
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    matcher.add_situations(example_data)

    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")