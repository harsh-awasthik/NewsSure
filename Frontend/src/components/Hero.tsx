import { Shield, Search, CheckCircle } from "lucide-react";
import newssureLogo from "@/assets/newssure_logo.jpg";

export const Hero = () => {
  return (
    <section className="relative overflow-hidden bg-gradient-hero py-20 md:py-28">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center justify-center mb-8 animate-float">
            <img src={newssureLogo} alt="NewsSure" className="h-32 w-32 object-contain" />
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <span className="bg-gradient-primary bg-clip-text text-transparent">
              NewsSure
            </span>
          </h1>
          
          <p className="text-2xl md:text-3xl font-semibold text-primary mb-6 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-150">
            Verify News, Trust Facts
          </p>
          
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300">
            Verify news and claims instantly with our AI-powered platform. Get truth scores, source credibility analysis, and detailed explanations in seconds.
          </p>
          
          <div className="grid md:grid-cols-3 gap-6 mt-12 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-500">
            <FeatureCard
              icon={<Search className="h-6 w-6" />}
              title="Real-time Verification"
              description="Instant fact-checking with AI-powered analysis"
            />
            <FeatureCard
              icon={<Shield className="h-6 w-6" />}
              title="Source Credibility"
              description="Analyze and rank source reliability"
            />
            <FeatureCard
              icon={<CheckCircle className="h-6 w-6" />}
              title="Transparent Results"
              description="Clear explanations for every verdict"
            />
          </div>
        </div>
      </div>
      
      {/* Background decoration */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-full opacity-30 pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-primary/20 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-72 h-72 bg-accent/20 rounded-full blur-3xl" />
      </div>
    </section>
  );
};

const FeatureCard = ({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) => {
  return (
    <div className="bg-card border border-border rounded-xl p-6 hover:shadow-lg-custom transition-all duration-300 hover:-translate-y-1">
      <div className="bg-primary/10 rounded-lg w-12 h-12 flex items-center justify-center text-primary mb-4">
        {icon}
      </div>
      <h3 className="font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
};
