export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-navy">
      <div className="w-10 h-10 border-4 border-brand-green border-t-transparent rounded-full animate-spin" />
    </div>
  );
}
