def recommend_jobs(skills):

    jobs = []

    if "Python" in skills:
        jobs.append("Python Developer")

    if "Java" in skills:
        jobs.append("Java Developer")

    if "SQL" in skills:
        jobs.append("Database Developer")

    if "MongoDB" in skills:
        jobs.append("Backend Developer")

    if "Python" in skills and "SQL" in skills:
        jobs.append("Software Developer")

    return list(set(jobs))