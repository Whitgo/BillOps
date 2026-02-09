/**
 * Form success alert component
 */

interface FormSuccessProps {
  message?: string | null;
}

export const FormSuccess = ({ message }: FormSuccessProps) => {
  if (!message) return null;

  return (
    <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
};
