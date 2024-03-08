import random
import time

from locust import HttpUser, between, task


class ChatUser(HttpUser):
    wait_time = between(5, 20)

    @task
    def ask_question(self):
        self.client.get("/")
        time.sleep(5)
        self.client.post(
            "/chat",
            json={
                "messages": [
                    {
                        "content": random.choice(
                            [
                                "What is Mosaic Theory?",
                                "Can you show me case examples related to Mosaic Theory?",
                                "Can you provide me with a quiz question related to Ethical Standard II(A) - Material Nonpublic Information?"",
                                "Can you give me one more quiz?",
                            ]
                        ),
                        "role": "user",
                    },
                ],
                "context": {
                    "overrides": {
                        "retrieval_mode": "hybrid",
                        "semantic_ranker": True,
                        "semantic_captions": False,
                        "top": 3,
                        "suggest_followup_questions": False,
                    },
                },
            },
        )
        time.sleep(5)
        self.client.post(
            "/chat",
            json={
                "messages": [
                    {"content": "What is Mosaic Theory?", "role": "user"},
                    {
                        "content": "Based on Mosaic Theory, a financial analyst may use significant conclusions derived from the analysis of public and nonmaterial nonpublic information as the basis for investment recommendations and decisions even if those conclusions would have been material inside information had they been communicated directly to the analyst by a company. Under the Mosaic Theory, financial analysts are free to act on this collection, or mosaic, of information without risking violation.",
                        "role": "assistant",
                    },
                    {"content": "Can you show me case examples related to Mosaic Theory?", "role": "user"},
                    {
                        "content": "Case Exmaple: Roger Clement is a senior financial analyst who specializes in the European automobile sector at Rivoli Capital.After speaking with representatives of Turgot Chariots—a European auto manufacturer with sales primarily in South Korea—and after conducting interviews with salespeople, labor leaders, his firm’s Korean currency analysts, and banking officials, Clement thinks the prospect of Turgot Chariots is not promising. He then changes his conclusion about the company from “market outperform” to “market underperform.” Clement retains the support material used to reach his conclusion in case questions later arise. Comment-To reach a conclusion about the value of the company, Clement has pieced together a number of nonmaterial or public bits of information that affect Turgot Chariots. Therefore, under the mosaic theory, Clement has not violated Standard II(A) in drafting the report.",
                        "role": "assistant",
                    },
                    {"content": "Can you provide me with a quiz question related to Ethical Standard II(A) - Material Nonpublic Information?", "role": "user"},
                    {
                        "content": "Winifred is an investment analyst who has accumulated and analyzed several pieces of nonpublic information through her contacts with drug firms. Although none of the information is"material," Winifred correctly concluded that the earnings of one of the drug firms would be unexpectedly high in the coming year. According to the Code and Standards, Winifred: A. can use the information to make investment recommendations and decisions. B. should publish the information before she uses it in her investment recommendations and decisions. C. should urge the drug firm to publicly disseminate the information immediately. Which one is the correct answer?",
                        "role": "assistant",
                    },
                ],
                "context": {
                    "overrides": {
                        "retrieval_mode": "hybrid",
                        "semantic_ranker": True,
                        "semantic_captions": False,
                        "top": 3,
                        "suggest_followup_questions": False,
                    },
                },
            },
        )
