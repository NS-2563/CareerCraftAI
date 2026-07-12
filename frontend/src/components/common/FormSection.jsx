export default function FormSection({ title, children }) {
  return (
    <div className="rounded-xl border p-5 space-y-4">
      <h3 className="font-semibold">{title}</h3>
      {children}
    </div>
  );
}



