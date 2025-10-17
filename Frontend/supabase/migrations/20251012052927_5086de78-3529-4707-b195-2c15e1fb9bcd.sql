-- Create verification_history table
CREATE TABLE public.verification_history (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  claim TEXT NOT NULL,
  truth_score INTEGER NOT NULL,
  verdict TEXT NOT NULL,
  sources JSONB,
  explanation TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.verification_history ENABLE ROW LEVEL SECURITY;

-- Create policies for user access
CREATE POLICY "Users can view their own verification history" 
ON public.verification_history 
FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own verification history" 
ON public.verification_history 
FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own verification history" 
ON public.verification_history 
FOR DELETE 
USING (auth.uid() = user_id);

-- Create index for better performance
CREATE INDEX idx_verification_history_user_id ON public.verification_history(user_id);
CREATE INDEX idx_verification_history_created_at ON public.verification_history(created_at DESC);