def generate_questions(skills):

    if isinstance(skills, list):
        skills = [s.lower() for s in skills]
    else:
        skills = skills.lower()

    questions = []

    if ("python" in skills):
        questions.append("Explain list and tuple differences in Python.")
        questions.append("What are decorators in Python?")

    if ("java" in skills):
        questions.append("What is the difference between JDK, JRE and JVM?")

    if ("sql" in skills):
        questions.append("Explain INNER JOIN and LEFT JOIN.")

    if ("mongodb" in skills):
        questions.append("Difference between MongoDB and MySQL?")

    questions.append("Tell me about yourself.")
    questions.append("Why should we hire you?")

    return questions