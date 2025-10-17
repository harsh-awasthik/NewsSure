// src/components/ShareButtons.tsx
import { useState, useRef } from 'react';
import { Download, Share2, MessageCircle, Instagram, Link2, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/hooks/use-toast';
import {
  downloadCardAsImage,
  shareToWhatsApp,
  shareToInstagram,
  shareCard,
  copyLinkToClipboard,
} from '@/lib/shareUtils';

interface ShareButtonsProps {
  cardRef: React.RefObject<HTMLElement>;
  title?: string;
  text?: string;
  filename?: string;
}

export const ShareButtons = ({
  cardRef,
  title = 'NewsSure Fact Check',
  text = 'Check out this fact-check result from NewsSure!',
  filename = 'NewsSure-card.png',
}: ShareButtonsProps) => {
  const [isSharing, setIsSharing] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const { toast } = useToast();

  const handleDownload = async () => {
    if (!cardRef.current) return;

    setIsSharing(true);
    const result = await downloadCardAsImage(cardRef.current, filename);
    setIsSharing(false);

    if (result.success) {
      toast({
        title: 'Downloaded!',
        description: 'Image saved to your device.',
      });
    } else {
      toast({
        title: 'Download failed',
        description: 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleWhatsAppShare = async () => {
    if (!cardRef.current) return;

    setIsSharing(true);
    const result = await shareToWhatsApp(cardRef.current, text);
    setIsSharing(false);

    if (!result.success) {
      toast({
        title: 'Share failed',
        description: 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleInstagramShare = async () => {
    if (!cardRef.current) return;

    setIsSharing(true);
    const result = await shareToInstagram(cardRef.current);
    setIsSharing(false);

    if (result.success && result.message) {
      toast({
        title: 'Image ready!',
        description: result.message,
      });
    } else if (!result.success) {
      toast({
        title: 'Share failed',
        description: 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleGenericShare = async () => {
    if (!cardRef.current) return;

    setIsSharing(true);
    const result = await shareCard(cardRef.current, title, text);
    setIsSharing(false);

    if (result.success && result.message) {
      toast({
        title: 'Success!',
        description: result.message,
      });
    } else if (!result.success) {
      toast({
        title: 'Share failed',
        description: 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleCopyLink = async () => {
    const result = await copyLinkToClipboard();

    if (result.success) {
      setLinkCopied(true);
      toast({
        title: 'Link copied!',
        description: 'Share link copied to clipboard.',
      });

      setTimeout(() => setLinkCopied(false), 2000);
    } else {
      toast({
        title: 'Copy failed',
        description: 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="flex gap-2 flex-wrap">
      {/* Download Button */}
      <Button
        onClick={handleDownload}
        disabled={isSharing}
        variant="outline"
        className="gap-2"
      >
        <Download className="w-4 h-4" />
        Download
      </Button>

      {/* Share Dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button disabled={isSharing} className="gap-2">
            <Share2 className="w-4 h-4" />
            Share
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuItem onClick={handleWhatsAppShare}>
            <MessageCircle className="w-4 h-4 mr-2" />
            Share to WhatsApp
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleInstagramShare}>
            <Instagram className="w-4 h-4 mr-2" />
            Share to Instagram
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleGenericShare}>
            <Share2 className="w-4 h-4 mr-2" />
            More options...
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleCopyLink}>
            {linkCopied ? (
              <Check className="w-4 h-4 mr-2 text-green-500" />
            ) : (
              <Link2 className="w-4 h-4 mr-2" />
            )}
            {linkCopied ? 'Copied!' : 'Copy Link'}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};