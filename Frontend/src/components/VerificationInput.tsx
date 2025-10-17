import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileText, Image as ImageIcon, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { ImageDragDrop } from '@/components/ImageDragDrop';

interface VerificationInputProps {
  onVerify: (input: string, type: 'text' | 'image') => void;
  isVerifying: boolean;
}

export const VerificationInput = ({ onVerify, isVerifying }: VerificationInputProps) => {
  const [textInput, setTextInput] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [activeTab, setActiveTab] = useState<'text' | 'image'>('text');

  const handleTextVerify = () => {
    if (!textInput.trim()) {
      toast.error("Please enter text to verify");
      return;
    }
    onVerify(textInput, 'text');
  };

const handleImageVerify = () => {
  if (!imageFile) {
    toast.error("Please upload an image to verify");
    return;
  }
  onVerify(imageFile as any, 'image'); // ✅ pass the actual File object
};

  const handleImageSelect = (file: File) => {
    setImageFile(file);
  };

  return (
    <Card className="p-6 max-w-4xl mx-auto shadow-lg-custom">
      <h2 className="text-2xl font-bold text-foreground mb-6">Verify a Claim</h2>
      
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'text' | 'image')} className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="text" className="gap-2">
            <FileText className="h-4 w-4" />
            Text Input
          </TabsTrigger>
          <TabsTrigger value="image" className="gap-2">
            <ImageIcon className="h-4 w-4" />
            Image Upload
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="text" className="space-y-4">
          <Textarea
            placeholder="Enter the claim or statement you want to verify..."
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            className="min-h-[150px] resize-none"
            disabled={isVerifying}
          />
          <Button
            onClick={handleTextVerify}
            disabled={isVerifying || !textInput.trim()}
            className="w-full bg-gradient-primary hover:opacity-90 transition-opacity"
            size="lg"
          >
            {isVerifying ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Verifying...
              </>
            ) : (
              "Verify Claim"
            )}
          </Button>
        </TabsContent>
        
        <TabsContent value="image" className="space-y-4">
          <ImageDragDrop 
            onImageSelect={handleImageSelect}
            maxSizeMB={10}
            acceptedFormats={['image/jpeg', 'image/png', 'image/jpg', 'image/webp']}
          />
          
          <Button
            onClick={handleImageVerify}
            disabled={isVerifying || !imageFile}
            className="w-full bg-gradient-primary hover:opacity-90 transition-opacity"
            size="lg"
          >
            {isVerifying ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing Image...
              </>
            ) : (
              "Analyze Image"
            )}
          </Button>
        </TabsContent>
      </Tabs>
    </Card>
  );
};