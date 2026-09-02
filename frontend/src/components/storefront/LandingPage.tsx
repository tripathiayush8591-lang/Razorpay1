import React from "react";
import Hero from "./Hero";
import FeaturedProducts from "./FeaturedProducts";
import HowItWorks from "./HowItWorks";
import TrustSection from "./TrustSection";

export const LandingPage: React.FC = () => {
  return (
    <div className="space-y-4">
      <Hero />
      <FeaturedProducts />
      <HowItWorks />
      <TrustSection />
    </div>
  );
};

export default LandingPage;
