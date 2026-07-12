import { useState } from "react";
import api from "./services/api";

function App() {

  const [file,setFile] = useState(null);
  const [result,setResult] = useState(null);
  const [jdText,setJdText] = useState("");
  const [jdResult,setJdResult] = useState(null);
  const [coachQuestion,setCoachQuestion] = useState("");
  const [coachResponse,setCoachResponse] = useState("");
  const [interviewSkills,setInterviewSkills] = useState("");
  const [questions,setQuestions] = useState([]);
  const [currentQuestion,setCurrentQuestion] = useState(0);
  const [answer,setAnswer] = useState("");
  const [evaluation,setEvaluation] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [jobRole, setJobRole] = useState("");
  const [optimizedResume, setOptimizedResume] = useState("");
  const [goal,setGoal] = useState("");
  const [roadmap,setRoadmap] = useState("");
  const [name,setName] = useState("");
  const [company,setCompany] = useState("");
  const [coverRole,setCoverRole] = useState("");
  const [coverSkills,setCoverSkills] = useState("");
  const [coverLetter,setCoverLetter] = useState("");

  const uploadResume = async () => {
    const formData = new FormData();
    formData.append("file",file);

    try{
      const response = await api.post("/upload-resume",formData,{
        headers:{ "Content-Type":"multipart/form-data" }
      });
      setResult(response.data);
    }catch(error){
      console.error(error);
    }
  };

  const analyzeJD = async () => {
    try{

      const jdSkills = jdText
        .split(/[\n,]/)
        .map(skill=>skill.trim())
        .filter(skill=>skill);

      const response = await api.post("/match-jd",{
        resume_skills: result.skills_found,
        jd_skills: jdSkills
      });

      setJdResult(response.data);

    }catch(error){
      console.error(error);
    }
  };

  const askCareerCoach = async () => {

  try {

    const response = await api.post(
      "/career-coach",
      { question: coachQuestion }
    );
    setCoachResponse(response.data.response);
  } catch(error) {
    console.error(error);
  }
};

const generateInterview = async () => {

  try {

    const skills = interviewSkills
      .split(",")
      .map(skill => skill.trim())
      .filter(skill => skill);

    const response = await api.post(
      "/generate-interview",
      { skills }
    );

    setQuestions(response.data.questions);
    setCurrentQuestion(0);

  } catch (error) {

    console.error(error);

  }

};

const evaluateAnswer = async () => {

  try{

    const response = await api.post(
      "/evaluate-answer",
      { answer }
    );

    setEvaluation(response.data);

  }catch(error){

    console.error(error);

  }

};

const optimizeResume = async () => {

  try {

    const response = await api.post("/optimize-resume", {
      resume: resumeText,
      job_role: jobRole
    });

    setOptimizedResume(response.data.optimized_resume);

  } catch (error) {
    console.error(error);
  }

};

const generateRoadmap = async () => {

  try{

    const response = await api.post("/career-roadmap",{
      goal
    });

    setRoadmap(response.data.roadmap);

  }catch(error){

    console.error(error);

  }

};

const generateCoverLetter = async () => {

  try{

    const response = await api.post("/cover-letter",{

      name,
      company,
      job_role: coverRole,
      skills: coverSkills

    });

    setCoverLetter(response.data.cover_letter);

  }catch(error){

    console.error(error);

  }

};


  return (

    <div style={{maxWidth:"1200px",margin:"auto",padding:"20px"}}>

      <h1 style={{textAlign:"center"}}>CareerCraft AI</h1>

      <div style={{display:"flex",flexDirection:"column",gap:"10px",marginBottom:"20px"}}>

        <input type="file" onChange={(e)=>setFile(e.target.files[0])}/>

        <textarea
          rows="6"
          value={jdText}
          onChange={(e)=>setJdText(e.target.value)}
          placeholder="Paste Job Description Skills (Python, Java, AWS...)"
        />

        <div style={{display:"flex",gap:"10px"}}>
          <button onClick={uploadResume}>Upload Resume</button>
          <button onClick={analyzeJD} disabled={!result}>Analyze JD Match</button>
        </div>

      </div>

      {result && (

        <>

          <div style={{display:"flex",gap:"20px",flexWrap:"wrap"}}>

            <div style={{border:"1px solid #ddd",padding:"20px",borderRadius:"10px",flex:"1"}}>
              <h3>ATS Score</h3>
              <h1>{result.ats_score}%</h1>
              <div style={{background:"#ddd",height:"10px",borderRadius:"10px"}}>
                <div style={{width:`${result.ats_score}%`,height:"10px",background:"green",borderRadius:"10px"}}/>
              </div>
            </div>

            <div style={{border:"1px solid #ddd",padding:"20px",borderRadius:"10px",flex:"1"}}>
              <h3>Career Readiness</h3>
              <h1>{result.career_readiness.career_readiness_score}%</h1>
              <div style={{background:"#ddd",height:"10px",borderRadius:"10px"}}>
                <div style={{width:`${result.career_readiness.career_readiness_score}%`,height:"10px",background:"green",borderRadius:"10px"}}/>
              </div>
              <p>{result.career_readiness.status}</p>
            </div>

            {result.employability_prediction && (
              <div style={{border:"1px solid #ddd",padding:"20px",borderRadius:"10px",flex:"1"}}>
                <h3>Employability</h3>
                <h1>{result.employability_prediction.score}%</h1>
                <p>{result.employability_prediction.status}</p>
                </div>
              )}

            {jdResult && (
              <div style={{border:"1px solid #ddd",padding:"20px",borderRadius:"10px",flex:"1"}}>
                <h3>JD Match</h3>
                <h1>{jdResult.match_score}%</h1>
              </div>
            )}

          </div>

          <div style={{display:"flex",gap:"40px",marginTop:"30px",flexWrap:"wrap"}}>

            <div style={{flex:"1"}}>
              <h2>Skills Found</h2>
              <ul>
                {result.skills_found.map((skill,index)=>(
                  <li key={index}>✅ {skill}</li>
                ))}
              </ul>
            </div>

            <div style={{flex:"1",textAlign:"left"}}>
              <h2>Missing Skills</h2>
              <ul>
                {result.skill_gap_report.missing_skills.map((skill,index)=>(
                  <li key={index}>❌ {skill}</li>
                ))}
              </ul>
            </div>

          </div>

          {jdResult && (

            <div style={{marginTop:"20px"}}>

              <h2>JD Analysis</h2>

              <h3>Matched Skills</h3>
              <ul style={{listStyle:"none",padding:0}}>
                {jdResult.matched_skills.map((skill,index)=>(
                  <li key={index}>✅ {skill}</li>
                ))}
              </ul>

              <h3>Missing Skills</h3>
              <ul style={{listStyle:"none",padding:0}}>
                {jdResult.missing_skills.map((skill,index)=>(
                  <li key={index}>❌ {skill}</li>
                ))}
              </ul>

            </div>

          )}

          <div style={{marginTop:"20px"}}>

            <h2>Suggestions</h2>

            <ul>
              {result.suggestions.map((item,index)=>(
                <li key={index}>{item}</li>
              ))}
            </ul>

          </div>

          <div style={{marginTop:"20px"}}>

            <h2>Learning Path</h2>

            <div style={{
              display:"grid",
              gridTemplateColumns:"repeat(auto-fit,minmax(250px,1fr))",
              gap:"20px"
            }}>

              {result.learning_path.map((item,index)=>(

                <div
                  key={index}
                  style={{
                    border:"1px solid #ddd",
                    borderRadius:"10px",
                    padding:"15px"
                  }}
                >
                  <h3>{item.skill}</h3>
                  <ul>
                    {item.resources.map((resource,i)=>(
                      <li key={i}>📚 {resource}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
            <div style={{
              marginTop:"30px",
              border:"1px solid #ddd",
              padding:"20px",
              borderRadius:"10px"
              }}>
                <h2>AI Career Coach</h2>
                <textarea
                rows="5"
                cols="80"
                value={coachQuestion}
                onChange={(e)=>setCoachQuestion(e.target.value)}
                placeholder="Ask anything about career, resume, interviews..."/>
                <br/><br/>
<button onClick={askCareerCoach}>
  Ask Coach
</button>

{coachResponse && (

  <div
    style={{
      marginTop: "20px",
      background: "#f5f5f5",
      padding: "15px",
      borderRadius: "10px",
    }}
  >
    <h3>Response</h3>

```
<pre
  style={{
    whiteSpace: "pre-wrap",
    fontFamily: "inherit",
  }}
>
  {coachResponse}
</pre>
```

  </div>
)}

<div
  style={{
    marginTop: "30px",
    border: "1px solid #ddd",
    padding: "20px",
    borderRadius: "10px",
  }}
>
  <h2>Mock Interview Simulator</h2>

<input
type="text"
value={interviewSkills}
onChange={(e) => setInterviewSkills(e.target.value)}
placeholder="Python, FastAPI, SQL"
style={{
width: "100%",
padding: "10px",
}}
/>

  <br />
  <br />

  <button onClick={generateInterview}>
    Generate Questions
  </button>

{questions.length > 0 && (
<div style={{ marginTop: "20px" }}> <h3>
Question {currentQuestion + 1} </h3>

```
  <p>{questions[currentQuestion]}</p>

  <textarea
    rows="5"
    value={answer}
    onChange={(e) => setAnswer(e.target.value)}
    placeholder="Type your answer here..."
    style={{ width: "100%" }}
  />

  <br />
  <br />

  <button onClick={evaluateAnswer}>
    Evaluate Answer
  </button>

  {evaluation && (
    <div
      style={{
        marginTop: "15px",
        background: "#f5f5f5",
        padding: "15px",
        borderRadius: "10px",
      }}
    >
      <h4>Score: {evaluation.score}</h4>

      <h4>Strengths</h4>
      <ul>
        {evaluation.strengths?.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ul>

      <h4>Improvements</h4>
      <ul>
        {evaluation.improvements?.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ul>
    </div>
  )}

  <br />
  <br />

  <button
    onClick={() => {
      setCurrentQuestion(currentQuestion + 1);
      setAnswer("");
      setEvaluation(null);
    }}
    disabled={currentQuestion === questions.length - 1}
  >
    Next Question
  </button>
</div>


)}

<div style={{
  marginTop: "30px",
  border: "1px solid #ddd",
  padding: "20px",
  borderRadius: "10px"
}}>

  <h2>AI Resume Optimizer</h2>

  <input
    type="text"
    value={jobRole}
    onChange={(e) => setJobRole(e.target.value)}
    placeholder="Target Job Role (Python Developer)"
    style={{
      width: "100%",
      padding: "10px",
      marginBottom: "15px"
    }}
  />

  <textarea
    rows="10"
    value={resumeText}
    onChange={(e) => setResumeText(e.target.value)}
    placeholder="Paste your resume here..."
    style={{
      width: "100%"
    }}
  />

  <br /><br />

  <button onClick={optimizeResume}>
    Optimize Resume
  </button>

  {optimizedResume && (

    <div style={{
      marginTop: "20px",
      background: "#f5f5f5",
      padding: "20px",
      borderRadius: "10px"
    }}>

      <h3>Optimized Resume</h3>

      <pre style={{
        whiteSpace: "pre-wrap",
        fontFamily: "inherit"
      }}>
        {optimizedResume}
      </pre>

    </div>

  )}

  <div style={{
  marginTop:"30px",
  border:"1px solid #ddd",
  padding:"20px",
  borderRadius:"10px"
}}>

<h2>AI Career Roadmap</h2>

<input
type="text"
value={goal}
onChange={(e)=>setGoal(e.target.value)}
placeholder="Example: Python Backend Developer"
style={{
width:"100%",
padding:"10px"
}}
/>

<br/><br/>

<button onClick={generateRoadmap}>
Generate Roadmap
</button>

{roadmap && (

<div style={{
marginTop:"20px",
background:"#f5f5f5",
padding:"20px",
borderRadius:"10px"
}}>

<pre style={{
whiteSpace:"pre-wrap",
fontFamily:"inherit"
}}>
{roadmap}
</pre>

</div>

)}

<div style={{
  marginTop:"30px",
  border:"1px solid #ddd",
  padding:"20px",
  borderRadius:"10px"
}}>

<h2>AI Cover Letter Generator</h2>

<input
placeholder="Your Name"
value={name}
onChange={(e)=>setName(e.target.value)}
style={{width:"100%",padding:"10px"}}
/>

<br/><br/>

<input
placeholder="Company"
value={company}
onChange={(e)=>setCompany(e.target.value)}
style={{width:"100%",padding:"10px"}}
/>

<br/><br/>

<input
placeholder="Job Role"
value={coverRole}
onChange={(e)=>setCoverRole(e.target.value)}
style={{width:"100%",padding:"10px"}}
/>

<br/><br/>

<textarea
rows="4"
placeholder="Skills"
value={coverSkills}
onChange={(e)=>setCoverSkills(e.target.value)}
style={{width:"100%"}}
/>

<br/><br/>

<button onClick={generateCoverLetter}>
Generate Cover Letter
</button>

{coverLetter && (

<div style={{
marginTop:"20px",
background:"#f5f5f5",
padding:"20px",
borderRadius:"10px"
}}>

<pre style={{
whiteSpace:"pre-wrap",
fontFamily:"inherit"
}}>
{coverLetter}
</pre>

</div>

)}

</div>

</div>

</div>

</div>

</div>
</div>

</>
)}

</div>

);
}

export default App;


