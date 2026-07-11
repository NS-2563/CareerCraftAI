def evaluate_answer(answer):

    score = min(len(answer.split()) * 2, 100)

    strengths = []
    improvements = []

    if len(answer.split()) > 30:
        strengths.append("Detailed response")
    else:
        improvements.append("Provide more detailed answers")

    if "example" in answer.lower():
        strengths.append("Used examples")
    else:
        improvements.append("Add practical examples")

    return {
        "score": score,
        "strengths": strengths,
        "improvements": improvements
    }