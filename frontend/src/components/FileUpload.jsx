import { useRef, useState } from "react";
import { Paperclip, X, CheckCircle } from "lucide-react";
import { uploadCSV } from "../services/api";

const FileUpload = ({ onFileUploaded, uploadedFile, onClearFile }) => {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith(".csv")) {
      showToast("Only CSV files are supported", "error");
      return;
    }

    setUploading(true);
    try {
      const result = await uploadCSV(file);
      // Pass both display name AND server filepath to parent
      const serverPath = result?.filepath || result?.path || result?.file_path || "";
      onFileUploaded(file.name, serverPath);
      showToast(`✓ ${file.name} uploaded successfully`);
    } catch (err) {
      showToast("Upload failed. Check backend connection.", "error");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={handleFileChange}
      />

      {toast && (
        <div className={`upload-toast upload-toast--${toast.type}`}>
          {toast.message}
        </div>
      )}

      {uploadedFile ? (
        <div className="uploaded-file-chip">
          <CheckCircle size={12} className="uploaded-file-chip__icon" />
          <span className="uploaded-file-chip__name">{uploadedFile}</span>
          <button
            className="uploaded-file-chip__remove"
            onClick={onClearFile}
            title="Remove file"
          >
            <X size={12} />
          </button>
        </div>
      ) : (
        <button
          className="upload-btn"
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          title="Upload CSV"
        >
          <Paperclip size={16} />
        </button>
      )}
    </>
  );
};

export default FileUpload;