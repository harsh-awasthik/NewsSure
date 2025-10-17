import { useState, useRef, DragEvent } from 'react';
import { Upload, X, Image as ImageIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  maxSizeMB?: number;
  acceptedFormats?: string[];
}

export const ImageDragDrop = ({ 
  onImageSelect, 
  maxSizeMB = 5,
  acceptedFormats = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
}: ImageUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    // Check file type
    if (!acceptedFormats.includes(file.type)) {
      toast.error('Invalid file format. Please upload a valid image.');
      return false;
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSizeMB) {
      toast.error(`File size must be less than ${maxSizeMB}MB`);
      return false;
    }

    return true;
  };

  const handleFile = (file: File) => {
    if (validateFile(file)) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
        setFileName(file.name);
      };
      reader.readAsDataURL(file);
      onImageSelect(file);
      toast.success('Image uploaded successfully!');
    }
  };

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleRemove = () => {
    setPreview(null);
    setFileName('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedFormats.join(',')}
        onChange={handleFileInput}
        className="hidden"
      />

      {!preview ? (
        <div
          onClick={handleClick}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
            transition-all duration-200 ease-in-out
            ${isDragging 
              ? 'border-primary bg-primary/10 scale-105' 
              : 'border-border bg-card hover:border-primary hover:bg-accent'
            }
          `}
        >
          <div className="flex flex-col items-center gap-4">
            <div className={`
              p-4 rounded-full transition-colors
              ${isDragging ? 'bg-primary/20' : 'bg-accent'}
            `}>
              <Upload className={`w-8 h-8 ${isDragging ? 'text-primary' : 'text-muted-foreground'}`} />
            </div>
            
            <div>
              <p className="text-lg font-semibold text-foreground mb-1">
                {isDragging ? 'Drop image here' : 'Drag & drop your image'}
              </p>
              <p className="text-sm text-muted-foreground mb-3">
                or click to browse
              </p>
              <p className="text-xs text-muted-foreground">
                Supported formats: JPEG, PNG, WebP (Max {maxSizeMB}MB)
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="border-2 border-border rounded-lg p-4 bg-card">
          <div className="flex items-start gap-4">
            <div className="relative flex-shrink-0">
              <img
                src={preview}
                alt="Preview"
                className="w-32 h-32 object-cover rounded-lg border border-border"
              />
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <ImageIcon className="w-5 h-5 text-primary flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {fileName}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Ready to verify
                    </p>
                  </div>
                </div>
                
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleRemove}
                  className="flex-shrink-0"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleClick}
                className="mt-3"
              >
                Change Image
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};