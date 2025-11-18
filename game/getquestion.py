from openai import OpenAI

__all__ = ["get_question", "convert"]


def get_question() -> str:
    client = OpenAI(
        api_key="sk-35740113636c45d1be0454f5beff359c",
        base_url="https://api.deepseek.com/v1",
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {
                "role": "user",
                "content": "我现在需要你帮我生成一道关于AI知识的选择题,难度低,共有四个选项,请按照题目\n选项(每个选项换行输出)\n答案序号(如A) 的格式输出,以下是一个例子:\n以下哪项是人工智能（AI）的主要目标？\nA 取代所有人类工作\nB 模拟、延伸和扩展人类智能\nC 制造具有情感的机器人\nD 实现计算机硬件的高速发展\n\nB",
            },
        ],
        stream=False,
    )

    return response.choices[0].message.content


def convert(s: str) -> dict[str, str | int]:
    s_c = s.split("\n")
    for num, c in enumerate(s_c):
        s_c[num] = c.strip()
    d: dict = {"question": s_c[0], "options": s_c[1:-2], "correct": ord(s_c[-1]) - 65}
    return d


if __name__ == "__main__":
    print(convert(get_question()))
