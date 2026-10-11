export default function Logo({
  href = "/",
  compact = false,
}: {
  href?: string;
  compact?: boolean;
}) {
  return (
    <a href={href} className="brand" aria-label="Subabot home">
      <span className="brand-icon" aria-hidden="true">
        <i />
        <i />
      </span>
      {!compact && (
        <span>
          subabot<span className="brand-period">.</span>
        </span>
      )}
    </a>
  );
}
