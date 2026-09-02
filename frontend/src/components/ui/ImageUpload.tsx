import React, { useState, useRef } from "react";
import { UploadCloud, Image as ImageIcon, X, RefreshCw, AlertCircle, Loader2 } from "lucide-react";
import clsx from "clsx";
import { Button } from "./Button";
import { apiClient, resolveImageUrl } from "@/lib/api/client";

export interface ImageUploadProps {
  label?: string;
  helperText?: string;
  value?: string; // Current image URL or relative static path
  onChange: (imageUrl: string, file?: File) => void;
  error?: string;
  disabled?: boolean;
}

const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
const ACCEPTED_EXTENSIONS = ".png, .jpg, .jpeg, .webp";
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB

export const ImageUpload: React.FC<ImageUploadProps> = ({
  label = "Product Image",
  helperText = "Supports PNG, JPG, or WebP up to 5 MB (saved to local disk)",
  value,
  onChange,
  error: externalError,
  disabled = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [internalError, setInternalError] = useState<string | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [selectedFileSize, setSelectedFileSize] = useState<string | null>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const validateAndUploadFile = async (file: File) => {
    setInternalError(null);

    // 1. Validate file type
    if (!ACCEPTED_TYPES.includes(file.type.toLowerCase())) {
      setInternalError("Unsupported file type. Please select a PNG, JPG, or WebP image.");
      return;
    }

    // 2. Validate file size (5MB max)
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setInternalError(
        `File size (${formatFileSize(file.size)}) exceeds the 5 MB limit. Please select a smaller file.`
      );
      return;
    }

    setSelectedFileName(file.name);
    setSelectedFileSize(formatFileSize(file.size));
    setUploading(true);

    try {
      // 3. Upload to local FastAPI multipart endpoint
      const res = await apiClient.uploadProductImage(file);
      if (res.success && res.data) {
        onChange(res.data.url, file);
      } else {
        setInternalError(res.error?.message || "Failed to upload image.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error uploading file to server.";
      setInternalError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      validateAndUploadFile(files[0]);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !uploading) {
      setDragOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);

    if (disabled || uploading) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndUploadFile(files[0]);
    }
  };

  const handleRemove = () => {
    setSelectedFileName(null);
    setSelectedFileSize(null);
    setInternalError(null);
    onChange("", undefined);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleTriggerPicker = () => {
    if (!disabled && !uploading && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const activeError = internalError || externalError;
  const hasImage = Boolean(value);
  const displayUrl = resolveImageUrl(value);

  return (
    <div className="w-full flex flex-col gap-1.5">
      {label && (
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-text-dark">{label}</label>
          <span className="text-[11px] text-text-muted">PNG, JPG, WebP (Max 5MB)</span>
        </div>
      )}

      {/* Hidden native Windows/OS file picker input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        onChange={handleFileChange}
        disabled={disabled || uploading}
        className="hidden"
        aria-label="Upload product image file"
      />

      {/* Content State: Has image (Preview mode) vs. Empty state (Dropzone) */}
      {hasImage ? (
        <div className="bg-surface border border-border rounded-xl p-3 shadow-xs flex flex-col sm:flex-row items-center gap-4">
          {/* Image Thumbnail Preview */}
          <div className="relative w-28 h-28 rounded-lg bg-surface-tertiary overflow-hidden shrink-0 border border-border">
            {uploading ? (
              <div className="w-full h-full flex flex-col items-center justify-center gap-1.5 bg-surface-secondary text-accent">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-[10px] font-semibold text-text-secondary">Saving...</span>
              </div>
            ) : (
              <img
                src={displayUrl}
                alt="Selected product preview"
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src =
                    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&auto=format&fit=crop&q=60";
                }}
              />
            )}
          </div>

          {/* Details & Actions */}
          <div className="flex-1 min-w-0 w-full flex flex-col justify-between h-28 py-0.5">
            <div>
              <div className="flex items-center gap-1.5 text-xs font-bold text-text-primary">
                <ImageIcon className="w-3.5 h-3.5 text-accent shrink-0" />
                <span className="truncate">{selectedFileName || value?.split("/").pop() || "Product Image"}</span>
              </div>
              {selectedFileSize && (
                <p className="text-[11px] font-mono text-text-muted mt-0.5">{selectedFileSize}</p>
              )}
              <p className="text-[11px] text-text-secondary mt-1">
                {uploading ? "Uploading file to server..." : "Saved to local server storage."}
              </p>
            </div>

            {/* Action Buttons: Replace & Remove */}
            <div className="flex items-center gap-2 pt-2 border-t border-border">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleTriggerPicker}
                disabled={disabled || uploading}
                loading={uploading}
                icon={<RefreshCw className="w-3 h-3" />}
                className="text-xs"
              >
                Replace Image
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleRemove}
                disabled={disabled || uploading}
                icon={<X className="w-3 h-3 text-error" />}
                className="text-xs text-error hover:bg-error-light"
              >
                Remove
              </Button>
            </div>
          </div>
        </div>
      ) : (
        /* Empty Upload Dropzone */
        <div
          onClick={handleTriggerPicker}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={clsx(
            "relative w-full border-2 border-dashed rounded-xl p-6 transition flex flex-col items-center justify-center text-center cursor-pointer select-none",
            dragOver
              ? "border-accent bg-accent-muted/40"
              : "border-border bg-surface-secondary/50 hover:bg-surface-secondary hover:border-border-strong",
            activeError && "border-error/60 bg-error-light/30",
            (disabled || uploading) && "opacity-50 cursor-not-allowed pointer-events-none"
          )}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              handleTriggerPicker();
            }
          }}
        >
          <div className="w-10 h-10 rounded-xl bg-surface border border-border flex items-center justify-center text-accent shadow-2xs mb-2">
            {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <UploadCloud className="w-5 h-5" />}
          </div>

          <div className="space-y-1">
            <p className="text-xs font-bold text-text-primary">
              {uploading ? "Uploading to local disk..." : (
                <>
                  <span className="text-accent hover:underline">Click to browse your PC</span> or drag and drop
                </>
              )}
            </p>
            <p className="text-[11px] text-text-secondary">{helperText}</p>
          </div>
        </div>
      )}

      {/* Validation Error Message */}
      {activeError ? (
        <div className="flex items-center gap-1.5 text-xs text-error mt-0.5">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{activeError}</span>
        </div>
      ) : null}
    </div>
  );
};

export default ImageUpload;
