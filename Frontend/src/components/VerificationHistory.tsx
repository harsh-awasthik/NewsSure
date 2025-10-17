import { useEffect, useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Clock, ExternalLink, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { Progress } from "./ui/progress";

interface HistoryItem {
  id: string;
  claim: string;
  truth_score: number;
  verdict: string;
  created_at: string;
}

export const VerificationHistory = () => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        setLoading(false);
        return;
      }

      const { data, error } = await supabase
        .from('verification_history')
        .select('id, claim, truth_score, verdict, created_at')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(10);

      if (error) throw error;
      setHistory(data || []);
    } catch (error) {
      console.error('Error fetching history:', error);
      toast.error("Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const { error } = await supabase
        .from('verification_history')
        .delete()
        .eq('id', id);

      if (error) throw error;
      
      setHistory(history.filter(item => item.id !== id));
      toast.success("Verification deleted");
    } catch (error) {
      console.error('Error deleting:', error);
      toast.error("Failed to delete verification");
    }
  };

  const getVerdictColor = (verdict: string) => {
    switch (verdict.toLowerCase()) {
      case 'true':
      case 'verified':
        return 'bg-green-500/20 text-green-700 dark:text-green-400 border-green-500/30';
      case 'false':
      case 'misleading':
        return 'bg-red-500/20 text-red-700 dark:text-red-400 border-red-500/30';
      case 'mixed':
      case 'partially true':
        return 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-muted text-muted-foreground border-muted';
    }
  };

  if (loading) {
    return (
      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle>Verification History</CardTitle>
          <CardDescription>Loading your verification history...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (history.length === 0) {
    return (
      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            Verification History
          </CardTitle>
          <CardDescription>Your verification history will appear here</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="border-primary/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary" />
          Verification History
        </CardTitle>
        <CardDescription>Your recent verifications</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {history.map((item) => (
          <div
            key={item.id}
            className="p-4 rounded-lg border border-border bg-card/50 hover:bg-card transition-colors space-y-3"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground line-clamp-2">
                  {item.claim}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {new Date(item.created_at).toLocaleDateString()} at{' '}
                  {new Date(item.created_at).toLocaleTimeString()}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => navigate(`/share/${item.id}`)}
                  className="h-8 w-8"
                >
                  <ExternalLink className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleDelete(item.id)}
                  className="h-8 w-8 text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-muted-foreground">Truth Score</span>
                  <span className="text-xs font-semibold text-foreground">{item.truth_score}%</span>
                </div>
                <Progress value={item.truth_score} className="h-2" />
              </div>
              <Badge className={getVerdictColor(item.verdict)}>
                {item.verdict}
              </Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};
