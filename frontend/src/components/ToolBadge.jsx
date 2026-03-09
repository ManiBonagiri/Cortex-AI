const TOOL_CONFIG = {
  // Original 4
  web_search:        { icon: "🔍", label: "Web Search",         color: "search"   },
  csv_analyzer:      { icon: "📊", label: "CSV Analyzer",        color: "csv"      },
  code_executor:     { icon: "🐍", label: "Code Executor",       color: "code"     },
  weather:           { icon: "🌤️", label: "Weather",             color: "weather"  },
  // New 10
  wikipedia_search:  { icon: "📚", label: "Wikipedia",           color: "wiki"     },
  calculator:        { icon: "🧮", label: "Calculator",          color: "calc"     },
  url_reader:        { icon: "🔗", label: "URL Reader",          color: "url"      },
  datetime_tool:     { icon: "🕐", label: "Date & Time",         color: "time"     },
  currency_converter:{ icon: "💱", label: "Currency",            color: "currency" },
  stock_price:       { icon: "📈", label: "Stock Price",         color: "stock"    },
  dictionary:        { icon: "📖", label: "Dictionary",          color: "dict"     },
  translator:        { icon: "🌐", label: "Translator",          color: "translate"},
  news_headlines:    { icon: "📰", label: "News",                color: "news"     },
  unit_converter:    { icon: "📐", label: "Unit Converter",      color: "unit"     },
};

const ToolBadge = ({ tool }) => {
  const config = TOOL_CONFIG[tool] || {
    icon: "⚙️", label: tool, color: "default",
  };

  return (
    <span className={`tool-badge tool-badge--${config.color}`}>
      <span className="tool-badge__icon">{config.icon}</span>
      <span className="tool-badge__label">{config.label}</span>
    </span>
  );
};

export default ToolBadge;