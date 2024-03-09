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
                        "content": "Good question! Mosaic Theory refers to .... In summary, Mosaic Theory is about...",
                        "role": "assistant",
                    },
                    {"content": "Can you show me an example related to Mosaic Theory?", "role": "user"},
                    {
                        "content": "Of course! Let's see this example:\n\nRoger Clement is a senior financial analyst who specializes in the European automobile sector at Rivoli Capital....\n\nAnalysis: to reach a conclusion about the value of the company, Clement has pieced together a number of nonmaterial or public bits of information that affect Turgot Chariots. Therefore, under the mosaic theory, Clement has not violated Standard II(A) in drafting the report.",
                        "role": "assistant",
                    },
                    {"content": "Can you provide me with a quiz related to Ethical Standard II(A) - Material Nonpublic Information?", "role": "user"},
                    {
                        "content": "Sure! Ready for the challenge?\n\nUnder the Code and Standards, which of the following investment risks is least likely required to be disclosed to clients?\nAnswer Choices:\nA. the use of leverage as part of the investment strategy.\nB. risks that are unknown to the investment adviser at the time of the recommendation.\nC.general market-related risks.\"\n\nWhich is the correct answer?"",
                        "role": "assistant",
                    },
                    {"content": "I still don't understand.", "role": "user"},
                    {
                        "content": "No worries! Let me give you a more concrete example to make it clearer. Imaging. you are .... Does it sound clear to you now? Free to ask if you have more questions.",
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
