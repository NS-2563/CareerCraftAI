export default function JobTableEmpty() {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="text-center">
        <div className="text-base font-medium">No job applications found</div>
        <div className="mt-2 text-sm text-muted-foreground">
          Add a job application to see it here.
        </div>
      </div>
    </div>
  );
}

