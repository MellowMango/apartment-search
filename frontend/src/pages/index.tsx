import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import Layout from '../components/Layout';
import { fetchProperties } from '../utils/supabase';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { ArrowRight, Star, MapPin, AlertCircle } from 'lucide-react';

// Define types for property and API form data
interface Property {
  id: string;
  name: string;
  address: string;
  price: number | null;
  units: number | null;
  status: string;
  image_url: string | null;
}

interface ApiFormData {
  name: string;
  company: string;
  email: string;
  useCase: string;
}

type ApiFormStatus = null | 'submitting' | 'success' | 'error';

export default function HomePage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [apiFormData, setApiFormData] = useState<ApiFormData>({
    name: '',
    company: '',
    email: '',
    useCase: ''
  });
  const [apiFormStatus, setApiFormStatus] = useState<ApiFormStatus>(null);

  useEffect(() => {
    async function loadProperties() {
      try {
        setLoading(true);
        // Fetch properties using our utility function - include those with missing coordinates
        const data = await fetchProperties({ 
          sortBy: 'created_at', 
          sortAsc: false,
          pageSize: 3,
          page: 1,
          filters: {},
          includeIncomplete: true, // Show properties even if they have missing coordinates
          includeResearch: true
        });
        
        console.log(`Loaded ${data.length} properties for homepage`);
        setProperties(data);
      } catch (error) {
        console.error('Error fetching properties:', error);
      } finally {
        setLoading(false);
      }
    }

    loadProperties();
  }, []);

  // Handle API form input changes
  const handleApiFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { id, value } = e.target;
    setApiFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  // Handle API form submission
  const handleApiFormSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setApiFormStatus('submitting');
    
    // Validate form
    if (!apiFormData.name || !apiFormData.email || !apiFormData.useCase) {
      alert('Please fill in all required fields');
      setApiFormStatus(null);
      return;
    }
    
    try {
      // In a real implementation, you'd send this data to your backend
      // For now we'll just simulate a successful submission
      console.log('API access request:', apiFormData);
      
      // Simulate server delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Show success message
      setApiFormStatus('success');
      
      // Clear form
      setApiFormData({
        name: '',
        company: '',
        email: '',
        useCase: ''
      });
      
      // Reset after 5 seconds
      setTimeout(() => {
        setApiFormStatus(null);
      }, 5000);
    } catch (error) {
      console.error('Error submitting API request:', error);
      setApiFormStatus('error');
    }
  };

  // Format price for display
  const formatPrice = (price: number | null): string => {
    if (!price) return 'Price on request';
    return price >= 1000000 
      ? `$${(price / 1000000).toFixed(1)}M` 
      : `$${(price / 1000).toFixed(0)}K`;
  };

  return (
    <Layout title="Acquire Apartments | Austin Multifamily Property Listings">
      {/* Hero Section with parallax effect and modern design */}
      <section className="relative min-h-[85vh] flex items-center bg-primary text-primary-foreground overflow-hidden">
        {/* Background layers for parallax effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-primary/95 via-primary/85 to-primary/75"></div>
        <div 
          className="absolute inset-0 bg-[url('/images/austin-skyline.jpg')] bg-cover bg-center mix-blend-overlay opacity-40 transform scale-110"
          style={{ 
            transform: 'scale(1.1)',
            backgroundAttachment: 'fixed'
          }}
        ></div>
        
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-24 bg-gradient-to-b from-primary to-transparent opacity-30"></div>
        <div className="absolute bottom-0 left-0 w-full h-24 bg-gradient-to-t from-primary to-transparent opacity-30"></div>
        
        {/* Badge with improved design */}
        <div className="absolute top-4 right-4 md:top-8 md:right-8 z-10">
          <div className="bg-secondary/90 backdrop-blur-sm text-secondary-foreground shadow-lg rounded-lg py-2.5 px-5 flex items-center space-x-2 border border-secondary-foreground/10">
            <Star className="w-4 h-4" />
            <span className="font-medium text-sm tracking-wide">Premium Access Required</span>
          </div>
        </div>
        
        <div className="relative container mx-auto px-4 py-24 sm:py-32 lg:py-40 flex flex-col items-center z-10">
          <div className="max-w-5xl mx-auto text-center">
            <div className="inline-flex items-center px-3 py-1 rounded-full border border-primary-foreground/20 bg-primary-foreground/10 text-primary-foreground/90 text-sm font-medium mb-6">
              <span className="relative flex h-2 w-2 mr-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              Austin's Premier Property Platform
            </div>
            
            <h1 className="text-4xl md:text-7xl font-extrabold tracking-tight text-center mb-6 leading-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-primary-foreground/80">
              Multifamily Property<br />Search Simplified
            </h1>
            
            <p className="text-xl md:text-2xl text-center max-w-3xl mx-auto mb-12 text-primary-foreground/90 leading-relaxed font-light">
              All major Austin broker listings in one powerful platform. Find your next investment opportunity faster and with complete market intelligence.
            </p>
            
            <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-6">
              <Button asChild size="lg" className="px-8 py-6 text-lg font-semibold shadow-lg hover:shadow-xl transition-all group">
                <Link href="/map" className="flex items-center">
                  Explore Properties
                  <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="bg-transparent/20 backdrop-blur-sm text-primary-foreground border-primary-foreground/40 hover:bg-primary-foreground/10 px-8 py-6 text-lg font-semibold">
                <Link href="/signup">Sign in to Access</Link>
              </Button>
            </div>
            
            {/* Feature badges */}
            <div className="mt-16 flex flex-wrap justify-center gap-3">
              <div className="bg-primary-foreground/10 backdrop-blur-sm border border-primary-foreground/10 rounded-full px-4 py-1.5 text-sm font-medium text-primary-foreground/90 flex items-center">
                <MapPin className="w-4 h-4 mr-1.5" /> 200+ Active Listings
              </div>
              <div className="bg-primary-foreground/10 backdrop-blur-sm border border-primary-foreground/10 rounded-full px-4 py-1.5 text-sm font-medium text-primary-foreground/90 flex items-center">
                <AlertCircle className="w-4 h-4 mr-1.5" /> Exclusive Off-Market Deals
              </div>
              <div className="bg-primary-foreground/10 backdrop-blur-sm border border-primary-foreground/10 rounded-full px-4 py-1.5 text-sm font-medium text-primary-foreground/90 flex items-center">
                <Star className="w-4 h-4 mr-1.5" /> Real-Time Updates
              </div>
            </div>
          </div>
        </div>
        
        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex flex-col items-center animate-bounce">
          <div className="text-primary-foreground/60 text-sm font-medium mb-2">Scroll to explore</div>
          <svg className="w-6 h-6 text-primary-foreground/60" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* Featured Properties Section with improved cards and animations */}
      <section className="py-24 bg-background">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-14">
            <div>
              <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-3">
                Featured Listings
              </div>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Exceptional Properties</h2>
              <p className="mt-2 text-muted-foreground max-w-2xl">
                Hand-selected multifamily investment opportunities in the Austin metro area
              </p>
            </div>
            <Link 
              href="/map" 
              className="group hidden md:flex items-center mt-4 md:mt-0 text-primary font-medium hover:underline"
            >
              View All Properties
              <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
          
          {loading ? (
            <div className="flex flex-col justify-center items-center h-80">
              <div className="animate-spin rounded-full h-12 w-12 border-2 border-primary border-t-transparent"></div>
              <p className="mt-4 text-muted-foreground">Loading featured properties...</p>
            </div>
          ) : properties.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {properties.map((property) => (
                <Card 
                  key={property.id} 
                  className="overflow-hidden group hover:shadow-xl transition-all duration-300 border-muted/50"
                >
                  <div className="h-64 bg-muted relative overflow-hidden">
                    {property.image_url ? (
                      <div className="w-full h-full transform group-hover:scale-105 transition-transform duration-500">
                        <Image 
                          src={property.image_url} 
                          alt={property.name || 'Property image'} 
                          className="w-full h-full object-cover"
                          width={500}
                          height={300}
                        />
                      </div>
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-primary/5 group-hover:bg-primary/10 transition-colors duration-300">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-16 h-16 text-primary/30 group-hover:text-primary/40 transition-colors duration-300">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
                        </svg>
                      </div>
                    )}
                    <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-black/0 via-black/0 to-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    <div className="absolute top-3 right-3 bg-primary text-primary-foreground text-xs font-medium py-1 px-3 rounded-full shadow-lg">
                      {property.status || 'Available'}
                    </div>
                    <div className="absolute bottom-3 left-3 right-3 transform translate-y-2 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300">
                      <Button 
                        asChild 
                        variant="secondary" 
                        className="w-full font-medium shadow-lg"
                      >
                        <Link href={`/properties/${property.id}`}>View Details</Link>
                      </Button>
                    </div>
                  </div>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xl font-bold tracking-tight group-hover:text-primary transition-colors duration-300">{property.name}</CardTitle>
                    <CardDescription className="flex items-start">
                      <MapPin className="mr-1 h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                      <span className="line-clamp-1">{property.address}</span>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pb-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Price</p>
                        <p className="font-semibold text-lg">{formatPrice(property.price)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Units</p>
                        <p className="font-semibold text-lg">{property.units || 'N/A'}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="py-20 text-center">
              <div className="bg-muted/50 rounded-lg p-8 max-w-md mx-auto">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 text-muted-foreground mx-auto mb-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z" />
                </svg>
                <p className="text-lg font-medium">No properties available</p>
                <p className="text-muted-foreground mt-2">Check back soon for new listings or sign up for alerts.</p>
              </div>
            </div>
          )}
          
          <div className="mt-10 text-center md:hidden">
            <Button asChild variant="outline">
              <Link href="/map" className="flex items-center">
                View All Properties
                <ArrowRight className="ml-2 w-4 h-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section with animated cards and improved visuals */}
      <section className="py-28 bg-muted/30 relative overflow-hidden">
        {/* Background decorative elements */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-primary/5 rounded-full"></div>
          <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-primary/5 rounded-full"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full h-full max-w-7xl mx-auto">
            <div className="w-full h-full bg-[url('/images/grid-pattern.svg')] bg-center opacity-5"></div>
          </div>
        </div>
        
        <div className="container mx-auto px-4 relative z-10">
          <div className="text-center max-w-3xl mx-auto mb-20">
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-3">
              How It Works
            </div>
            <h2 className="text-4xl font-bold tracking-tight mb-6">Streamline Your Property Search</h2>
            <p className="text-xl text-muted-foreground">
              We aggregate multifamily property listings from all major brokers into one powerful platform, 
              saving you time and providing complete market intelligence.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-y-16 md:gap-x-8 lg:gap-x-16">
            {/* Feature 1 */}
            <div className="relative group">
              {/* Animated background */}
              <div className="absolute -inset-4 rounded-xl bg-gradient-to-r from-primary/5 to-primary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-lg"></div>
              
              {/* Feature card */}
              <div className="relative bg-background rounded-xl border border-muted shadow-lg group-hover:shadow-xl transition-all duration-300 p-8">
                <div className="relative">
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/15 transition-colors duration-300">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.75} stroke="currentColor" className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
                    </svg>
                  </div>
                  
                  <h3 className="text-xl font-semibold mb-3 group-hover:text-primary transition-colors duration-300">
                    Comprehensive Data
                  </h3>
                  
                  <p className="text-muted-foreground leading-relaxed mb-6">
                    Access listings from all major brokers in Austin in one place. No more jumping between 
                    websites or signing up for multiple newsletters.
                  </p>
                  
                  <ul className="space-y-2">
                    {['CBRE', 'Marcus & Millichap', 'JLL', 'Cushman & Wakefield'].map((broker, idx) => (
                      <li key={idx} className="flex items-center text-sm">
                        <svg className="w-5 h-5 text-primary mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>{broker}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
            
            {/* Feature 2 */}
            <div className="relative group">
              {/* Animated background */}
              <div className="absolute -inset-4 rounded-xl bg-gradient-to-r from-primary/5 to-primary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-lg"></div>
              
              {/* Feature card */}
              <div className="relative bg-background rounded-xl border border-muted shadow-lg group-hover:shadow-xl transition-all duration-300 p-8">
                <div className="relative">
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/15 transition-colors duration-300">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.75} stroke="currentColor" className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
                    </svg>
                  </div>
                  
                  <h3 className="text-xl font-semibold mb-3 group-hover:text-primary transition-colors duration-300">
                    Interactive Map
                  </h3>
                  
                  <p className="text-muted-foreground leading-relaxed mb-6">
                    Visualize all properties on our interactive map. Apply advanced filters to find exactly 
                    what you're looking for in your target areas.
                  </p>
                  
                  <ul className="space-y-2">
                    {['Location filtering', 'Price range search', 'Unit count filtering', 'Custom map views'].map((feature, idx) => (
                      <li key={idx} className="flex items-center text-sm">
                        <svg className="w-5 h-5 text-primary mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
            
            {/* Feature 3 */}
            <div className="relative group">
              {/* Animated background */}
              <div className="absolute -inset-4 rounded-xl bg-gradient-to-r from-primary/5 to-primary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-lg"></div>
              
              {/* Feature card */}
              <div className="relative bg-background rounded-xl border border-muted shadow-lg group-hover:shadow-xl transition-all duration-300 p-8">
                <div className="relative">
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/15 transition-colors duration-300">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.75} stroke="currentColor" className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                    </svg>
                  </div>
                  
                  <h3 className="text-xl font-semibold mb-3 group-hover:text-primary transition-colors duration-300">
                    Smart Notifications
                  </h3>
                  
                  <p className="text-muted-foreground leading-relaxed mb-6">
                    Stay informed with real-time alerts about new properties, price changes, and market trends 
                    that match your investment criteria.
                  </p>
                  
                  <ul className="space-y-2">
                    {['Email alerts', 'Custom saved searches', 'Price drop notifications', 'New listing alerts'].map((feature, idx) => (
                      <li key={idx} className="flex items-center text-sm">
                        <svg className="w-5 h-5 text-primary mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
          
          {/* API Access Teaser with improved design */}
          <div className="mt-24 rounded-2xl p-10 bg-gradient-to-br from-primary/5 via-primary/10 to-primary/5 border border-primary/20 backdrop-blur-sm">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-8">
              <div className="space-y-4 max-w-2xl">
                <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/20 text-primary text-sm font-medium">
                  Coming Soon
                </div>
                <h3 className="text-2xl font-semibold">Developer API Access</h3>
                <p className="text-muted-foreground text-lg leading-relaxed">
                  Integrate our comprehensive property data directly into your applications and workflows. 
                  Perfect for investment firms, developers, and real estate technology companies looking to 
                  leverage Austin's most complete multifamily database.
                </p>
              </div>
              <div className="flex-shrink-0">
                <Button 
                  asChild 
                  variant="outline" 
                  size="lg"
                  className="group font-medium rounded-xl"
                >
                  <Link 
                    href="#api-contact" 
                    onClick={(e) => {
                      e.preventDefault();
                      document.getElementById('api-contact')?.scrollIntoView({ behavior: 'smooth' });
                    }}
                    className="flex items-center"
                  >
                    Request Early Access
                    <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced CTA Section with modern design */}
      <section className="py-28 bg-primary relative overflow-hidden">
        {/* Decorative background elements */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-[url('/images/pattern.svg')] opacity-10"></div>
          <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-primary to-transparent"></div>
          <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-primary to-transparent"></div>
        </div>
        
        {/* Floating shapes */}
        <div className="absolute top-20 left-10 w-64 h-64 rounded-full bg-primary-foreground/5 blur-3xl"></div>
        <div className="absolute bottom-20 right-10 w-64 h-64 rounded-full bg-primary-foreground/5 blur-3xl"></div>
        
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-4xl mx-auto">
            <div className="bg-primary-foreground/10 backdrop-blur-sm border border-primary-foreground/10 rounded-3xl p-12 text-center">
              <div className="inline-flex items-center px-4 py-1.5 rounded-full bg-primary-foreground/20 text-primary-foreground mb-6 backdrop-blur-sm">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Get Started Today
              </div>
              
              <h2 className="text-4xl md:text-5xl font-bold mb-6 text-primary-foreground leading-tight">
                Ready to transform your<br />property search experience?
              </h2>
              
              <p className="text-xl mb-10 text-primary-foreground/90 max-w-2xl mx-auto leading-relaxed">
                Join thousands of investors who are already using our platform to find their next multifamily opportunity faster and with better data.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
                <Button 
                  asChild 
                  size="lg" 
                  variant="secondary" 
                  className="px-10 py-7 text-lg font-semibold shadow-2xl hover:shadow-lg transition-all w-full sm:w-auto group"
                >
                  <Link href="/signup" className="flex items-center justify-center">
                    Create Free Account
                    <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </Button>
                
                <Button 
                  asChild 
                  size="lg" 
                  variant="outline" 
                  className="bg-transparent text-primary-foreground border-primary-foreground/40 hover:bg-primary-foreground/10 px-10 py-7 text-lg font-semibold w-full sm:w-auto"
                >
                  <Link href="/map">Browse Properties</Link>
                </Button>
              </div>
              
              <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-5 text-primary-foreground/80">
                <div className="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span>Bank-level security</span>
                </div>
                <div className="hidden sm:block">•</div>
                <div className="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Setup in minutes</span>
                </div>
                <div className="hidden sm:block">•</div>
                <div className="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>Cancel anytime</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* API Contact Section with improved design */}
      <section id="api-contact" className="py-24 bg-background relative">
        {/* Background decorative elements */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-[10%] -right-[10%] w-[40%] h-[40%] rounded-full bg-primary/5 blur-3xl opacity-50"></div>
          <div className="absolute -bottom-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-primary/5 blur-3xl opacity-50"></div>
        </div>
        
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-12">
              <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-3">
                Developer Access
              </div>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">Request API Access</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Interested in integrating our property data into your applications?
                Join our early access program and be the first to leverage our comprehensive API.
              </p>
            </div>
            
            <Card className="border-muted/50 shadow-lg">
              <CardContent className="pt-6 px-6 sm:px-8 md:px-10">
                <form className="space-y-6" onSubmit={(e) => {
                  e.preventDefault();
                  handleApiFormSubmit(e);
                }}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label htmlFor="name" className="block text-sm font-medium">Full Name <span className="text-red-500">*</span></label>
                      <input 
                        id="name" 
                        type="text" 
                        className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary/50 focus:outline-none transition-all"
                        placeholder="John Smith"
                        value={apiFormData.name}
                        onChange={handleApiFormChange}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <label htmlFor="company" className="block text-sm font-medium">Company Name</label>
                      <input 
                        id="company" 
                        type="text" 
                        className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary/50 focus:outline-none transition-all"
                        placeholder="Your Company LLC"
                        value={apiFormData.company}
                        onChange={handleApiFormChange}
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <label htmlFor="email" className="block text-sm font-medium">Email Address <span className="text-red-500">*</span></label>
                    <input 
                      id="email" 
                      type="email" 
                      className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary/50 focus:outline-none transition-all"
                      placeholder="your@email.com"
                      value={apiFormData.email}
                      onChange={handleApiFormChange}
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label htmlFor="useCase" className="block text-sm font-medium">Intended API Use Case <span className="text-red-500">*</span></label>
                    <textarea 
                      id="useCase" 
                      className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary/50 focus:outline-none transition-all h-32 resize-none"
                      placeholder="Please describe how you intend to use our API and what features would be most valuable to you."
                      value={apiFormData.useCase}
                      onChange={handleApiFormChange}
                      required
                    />
                  </div>
                  
                  <div>
                    <Button 
                      type="submit" 
                      className="w-full py-6 text-base font-medium" 
                      disabled={apiFormStatus === 'submitting'}
                      size="lg"
                    >
                      {apiFormStatus === 'submitting' ? (
                        <span className="flex items-center justify-center">
                          <svg className="animate-spin -ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Processing Request...
                        </span>
                      ) : 'Request API Access'}
                    </Button>
                  </div>
                  
                  {apiFormStatus === 'success' && (
                    <div className="p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg flex items-start mt-6">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mt-0.5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <p className="font-medium">Thank you for your interest!</p>
                        <p className="mt-1 text-sm">We've received your request and will be in touch soon about our API program and early access opportunities.</p>
                      </div>
                    </div>
                  )}
                  
                  {apiFormStatus === 'error' && (
                    <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-start mt-6">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mt-0.5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <p className="font-medium">Submission Error</p>
                        <p className="mt-1 text-sm">There was a problem submitting your request. Please try again or contact us directly at api@acquire-apartments.com.</p>
                      </div>
                    </div>
                  )}
                  
                  <div className="pt-2 text-center">
                    <p className="text-sm text-muted-foreground">
                      By submitting this form, you agree to our{' '}
                      <Link href="/terms" className="text-primary hover:underline">Terms of Service</Link>{' '}
                      and{' '}
                      <Link href="/privacy" className="text-primary hover:underline">Privacy Policy</Link>.
                    </p>
                  </div>
                </form>
              </CardContent>
            </Card>
            
            <div className="mt-12 text-center">
              <p className="text-sm text-muted-foreground">
                Have questions about our API? Contact us at{' '}
                <a href="mailto:api@acquire-apartments.com" className="text-primary hover:underline">
                  api@acquire-apartments.com
                </a>
              </p>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
} 