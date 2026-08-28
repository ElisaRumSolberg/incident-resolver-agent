export function Logo({ size = "md" }: { size?: "sm" | "md" }) {
  const mark = size === "sm" ? 28 : 36;
  const glyph = size === "sm" ? 15 : 19;
  const text = size === "sm" ? "text-sm" : "text-base";

  return (
    <div className="flex items-center gap-2.5">
      <div
        className="flex flex-shrink-0 items-center justify-center rounded-xl shadow-lg shadow-black/20"
        style={{ width: mark, height: mark, background: "linear-gradient(135deg, var(--color-primary), var(--color-blocked))" }}
      >
        <svg width={glyph} height={glyph} viewBox="0 0 24 24" fill="none">
          <path
            d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z"
            stroke="white"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path d="M13 7.5l-3.4 5H12l-0.9 4L14.5 11H12l1-3.5z" fill="white" />
        </svg>
      </div>
      <div className={`${text} font-bold leading-none text-[var(--color-text-primary)]`}>
        Incident{" "}
        <span
          className="bg-clip-text text-transparent"
          style={{ backgroundImage: "linear-gradient(90deg, var(--color-primary), var(--color-blocked))" }}
        >
          Resolver
        </span>
      </div>
    </div>
  );
}
