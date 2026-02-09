/**
 * Form error alert component
 */

interface FormErrorProps {
  message?: string | null;
}

export const FormError = ({ message }: FormErrorProps) => {
  if (!message) return null;

  return (
    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
};
