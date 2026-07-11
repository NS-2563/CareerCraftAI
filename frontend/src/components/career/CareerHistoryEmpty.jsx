import { FolderSearch } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function CareerHistoryEmpty() {

    const navigate = useNavigate();

    return (

<div className="rounded-2xl border border-dashed p-16 text-center">

<FolderSearch
size={70}
className="mx-auto text-gray-400"
/>

<h2 className="text-2xl font-bold mt-6">

No Career Reports Yet

</h2>

<p className="text-gray-500 mt-3">

Complete your first assessment to start tracking your progress.

</p>

<button
onClick={()=>navigate("/career")}
className="mt-8 rounded-xl bg-primary text-primary-foreground px-6 py-3"
>

Take Assessment

</button>

</div>

    );
}