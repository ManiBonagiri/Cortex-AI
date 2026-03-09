import { useState } from "react";
import { ChevronDown, ChevronRight, Cpu } from "lucide-react";

const ThinkingSteps = ({ steps, latencyMs }) => {
  const [expanded, setExpanded] = useState(false);

  if (!steps || steps === 0) return null;

  return (
    <div className="thinking-steps">
      <button
        className="thinking-steps__toggle"
        onClick={() => setExpanded(!expanded)}
      >
        <Cpu size={12} className="thinking-steps__icon" />
        <span className="thinking-steps__summary">
          Agent reasoned through{" "}
          <span className="thinking-steps__count">{steps} step{steps !== 1 ? "s" : ""}</span>
        </span>
        {latencyMs && (
          <span className="thinking-steps__latency">
            {(latencyMs / 1000).toFixed(2)}s
          </span>
        )}
        {expanded ? (
          <ChevronDown size={12} className="thinking-steps__chevron" />
        ) : (
          <ChevronRight size={12} className="thinking-steps__chevron" />
        )}
      </button>

      {expanded && (
        <div className="thinking-steps__detail">
          {Array.from({ length: steps }, (_, i) => (
            <div key={i} className="thinking-steps__step">
              <span className="thinking-steps__step-dot" />
              <span className="thinking-steps__step-label">
                Step {i + 1} — Agent reasoning cycle
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ThinkingSteps;