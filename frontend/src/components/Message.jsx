import ReactMarkdown from "react-markdown";
import ToolBadge from "./ToolBadge";
import ThinkingSteps from "./ThinkingSteps";

const formatTime = (date) => {
  return new Date(date).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const UserMessage = ({ message }) => (
  <div className="message message--user">
    <div className="message__bubble message__bubble--user">
      <p className="message__text">{message.content}</p>
      <span className="message__time">{formatTime(message.timestamp)}</span>
    </div>
    <div className="message__avatar message__avatar--user">
      <span>U</span>
    </div>
  </div>
);

const AssistantMessage = ({ message }) => (
  <div className="message message--assistant">
    <div className="message__avatar message__avatar--assistant">
      <span className="message__avatar-glyph">⬡</span>
    </div>
    <div className="message__body">
      <div className="message__bubble message__bubble--assistant">
        <div className="message__markdown">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        <span className="message__time">{formatTime(message.timestamp)}</span>
      </div>

      {message.tools_used && message.tools_used.length > 0 && (
        <div className="message__tools">
          {message.tools_used.map((tool, i) => (
            <ToolBadge key={i} tool={tool} />
          ))}
        </div>
      )}

      <ThinkingSteps steps={message.steps} latencyMs={message.latency_ms} />
    </div>
  </div>
);

const TypingIndicator = () => (
  <div className="message message--assistant">
    <div className="message__avatar message__avatar--assistant">
      <span className="message__avatar-glyph">⬡</span>
    </div>
    <div className="message__bubble message__bubble--assistant message__bubble--typing">
      <div className="typing-dots">
        <span />
        <span />
        <span />
      </div>
      <span className="typing-label">Cortex is thinking...</span>
    </div>
  </div>
);

const Message = ({ message, isTyping }) => {
  if (isTyping) return <TypingIndicator />;
  if (message.role === "user") return <UserMessage message={message} />;
  return <AssistantMessage message={message} />;
};

export default Message;