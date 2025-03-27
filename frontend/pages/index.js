import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Layout from '../src/components/Layout';
import { fetchProperties } from '../lib/supabase';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';

export default function HomePage() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiFormData, setApiFormData] = useState({
    name: '',
    company: '',
    email: '',
    useCase: ''
  });
  const [apiFormStatus, setApiFormStatus] = useState(null); // null, 'submitting', 'success', 'error'

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
  const handleApiFormChange = (e) => {
    const { id, value } = e.target;
    setApiFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  // Handle API form submission
  const handleApiFormSubmit = async (e) => {
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
  const formatPrice = (price) => {
    if (!price) return 'Price on request';
    return price >= 1000000 
      ? `$${(price / 1000000).toFixed(1)}M` 
      : `$${(price / 1000).toFixed(0)}K`;
  };

  return (
    <Layout title="Acquire Apartments | Austin Multifamily Property Listings">
      {/* Hero Section with improved background and messaging */}
      <section className="relative bg-primary text-primary-foreground">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/90 via-primary/80 to-primary/70 opacity-90"></div>
        <div className="absolute inset-0 bg-[url('/images/austin-skyline.jpg')] bg-cover bg-center mix-blend-overlay opacity-30"></div>
        
        {/* Alpha Access Badge */}
        <div className="absolute top-4 right-4 md:top-8 md:right-8 z-10">
          <div className="bg-secondary text-secondary-foreground shadow-lg rounded-lg py-2 px-4 flex items-center space-x-2">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
            </svg>
            <span className="font-semibold text-sm">Login Required for Access</span>
          </div>
        </div>
        
        <div className="relative container mx-auto px-4 py-28 sm:px-6 lg:px-8 flex flex-col items-center">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-center mb-6 leading-tight">
              Austin's Multifamily Property Search Aggregator
            </h1>
            <p className="text-xl md:text-2xl text-center max-w-3xl mx-auto mb-10 text-primary-foreground/90 leading-relaxed">
              One platform to discover properties from all major brokers in Austin. Save time and find your next investment opportunity faster.
            </p>
            <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-6">
              <Button asChild size="lg" className="px-8 py-6 text-lg font-semibold shadow-lg hover:shadow-xl transition-all">
                <Link href="/map">Explore Properties</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="bg-transparent text-primary-foreground border-primary-foreground/40 hover:bg-primary-foreground/10 px-8 py-6 text-lg font-semibold">
                <Link href="/signup">Sign in to Access</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Properties Section */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center mb-12">
            <h2 className="text-3xl font-bold">Featured Properties</h2>
            <Link href="/map" className="text-primary font-medium flex items-center hover:underline">
              View All Properties
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 ml-1">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          </div>
          
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
            </div>
          ) : properties.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {properties.map((property) => (
                <Card key={property.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                  <div className="h-48 bg-gray-200 relative">
                    {property.image_url ? (
                      <img 
                        src={property.image_url} 
                        alt={property.name} 
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-primary/10">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 text-primary/50">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
                        </svg>
                      </div>
                    )}
                    <div className="absolute top-2 right-2 bg-primary text-primary-foreground text-xs font-semibold py-1 px-2 rounded">
                      {property.status || 'Available'}
                    </div>
                  </div>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xl">{property.name}</CardTitle>
                    <CardDescription>{property.address}</CardDescription>
                  </CardHeader>
                  <CardContent className="pb-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Price</p>
                        <p className="font-semibold">{formatPrice(property.price)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Units</p>
                        <p className="font-semibold">{property.units || 'N/A'}</p>
                      </div>
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button asChild variant="outline" className="w-full">
                      <Link href={`/properties/${property.id}`}>View Details</Link>
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p>No properties available. Check back soon!</p>
            </div>
          )}
        </div>
      </section>

      {/* Features Section with enhanced visuals */}
      <section className="py-20 bg-muted">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-4">How It Works</h2>
          <p className="text-xl text-center text-muted-foreground max-w-3xl mx-auto mb-16">
            We aggregate multifamily property listings directly from brokers into one searchable platform
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <Card className="bg-background border-none shadow-lg hover:shadow-xl transition-all">
              <CardHeader className="text-center">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-primary">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
                  </svg>
                </div>
                <CardTitle>Data From All Brokers</CardTitle>
                <CardDescription className="text-lg">One platform, multiple sources</CardDescription>
              </CardHeader>
              <CardContent>
                <p>We pull multifamily property listings directly from major brokers in Austin, so you don't have to visit multiple websites or sign up for different newsletters.</p>
              </CardContent>
            </Card>
            
            <Card className="bg-background border-none shadow-lg hover:shadow-xl transition-all">
              <CardHeader className="text-center">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-primary">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
                  </svg>
                </div>
                <CardTitle>Interactive Map</CardTitle>
                <CardDescription className="text-lg">Visualize property locations</CardDescription>
              </CardHeader>
              <CardContent>
                <p>See all available properties on our interactive map. Filter by location, price, number of units, and other criteria to find exactly what you're looking for.</p>
              </CardContent>
            </Card>
            
            <Card className="bg-background border-none shadow-lg hover:shadow-xl transition-all">
              <CardHeader className="text-center">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-primary">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                  </svg>
                </div>
                <CardTitle>Comprehensive Details</CardTitle>
                <CardDescription className="text-lg">All the information you need</CardDescription>
              </CardHeader>
              <CardContent>
                <p>Get detailed property information including price, unit mix, cap rate, and location details - all in one place without having to contact multiple brokers for basic information.</p>
              </CardContent>
            </Card>
          </div>
          
          {/* API Access Teaser */}
          <div className="mt-16 p-6 bg-primary/5 border border-primary/20 rounded-lg">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-3">
                <div className="inline-block bg-primary/10 text-primary text-xs font-semibold py-1 px-3 rounded-full">Coming Soon</div>
                <h3 className="text-xl font-semibold">API Access</h3>
                <p className="text-muted-foreground max-w-xl">
                  Integrate our property data directly into your applications and workflows. 
                  Perfect for investment firms, developers, and real estate technology companies.
                </p>
              </div>
              <Button asChild variant="outline" className="whitespace-nowrap">
                <Link href="#api-contact" onClick={(e) => {
                  e.preventDefault();
                  document.getElementById('api-contact').scrollIntoView({ 
                    behavior: 'smooth' 
                  });
                }}>Request API Access</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced CTA Section */}
      <section className="py-20 bg-primary text-primary-foreground relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/images/pattern.svg')] opacity-10"></div>
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-4xl font-bold mb-6">Ready to streamline your property search?</h2>
            <p className="text-xl mb-10 text-primary-foreground/90">
              Sign in with Google or email to access Austin's most comprehensive multifamily property database.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-6">
              <Button asChild size="lg" variant="secondary" className="px-10 py-6 text-lg font-semibold shadow-xl hover:shadow-2xl transition-all">
                <Link href="/signup">Sign Up / Login</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="bg-transparent text-primary-foreground border-primary-foreground/40 hover:bg-primary-foreground/10 px-10 py-6 text-lg font-semibold">
                <Link href="/map">Browse Properties</Link>
              </Button>
            </div>
            <p className="mt-6 text-primary-foreground/80 text-sm">
              Sign in with Google or email to access the platform.
            </p>
          </div>
        </div>
      </section>
      
      {/* API Contact Section */}
      <section id="api-contact" className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-4">Request API Access</h2>
              <p className="text-muted-foreground">
                Interested in accessing our property data via API? Let us know and we'll keep you updated.
              </p>
            </div>
            
            <Card>
              <CardContent className="pt-6">
                <form className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label htmlFor="name" className="text-sm font-medium">Full Name</label>
                      <input 
                        id="name" 
                        type="text" 
                        className="w-full p-2 border rounded-md"
                        placeholder="Your name"
                        value={apiFormData.name}
                        onChange={handleApiFormChange}
                      />
                    </div>
                    <div className="space-y-2">
                      <label htmlFor="company" className="text-sm font-medium">Company</label>
                      <input 
                        id="company" 
                        type="text" 
                        className="w-full p-2 border rounded-md"
                        placeholder="Your company name"
                        value={apiFormData.company}
                        onChange={handleApiFormChange}
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <label htmlFor="email" className="text-sm font-medium">Email Address</label>
                    <input 
                      id="email" 
                      type="email" 
                      className="w-full p-2 border rounded-md"
                      placeholder="your@email.com"
                      value={apiFormData.email}
                      onChange={handleApiFormChange}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label htmlFor="useCase" className="text-sm font-medium">Intended API Use Case</label>
                    <textarea 
                      id="useCase" 
                      className="w-full p-2 border rounded-md h-24"
                      placeholder="Please describe how you intend to use our API"
                      value={apiFormData.useCase}
                      onChange={handleApiFormChange}
                    />
                  </div>
                  
                  <div className="pt-2">
                    <Button 
                      type="submit" 
                      className="w-full" 
                      disabled={apiFormStatus === 'submitting'}
                      onClick={handleApiFormSubmit}
                    >
                      {apiFormStatus === 'submitting' ? (
                        <span className="flex items-center">
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Submitting...
                        </span>
                      ) : 'Submit Request'}
                    </Button>
                  </div>
                  
                  {apiFormStatus === 'success' && (
                    <div className="p-3 bg-green-50 text-green-700 rounded-md text-center">
                      Thank you! We've received your request and will be in touch soon.
                    </div>
                  )}
                  
                  {apiFormStatus === 'error' && (
                    <div className="p-3 bg-red-50 text-red-700 rounded-md text-center">
                      There was a problem submitting your request. Please try again.
                    </div>
                  )}
                  
                  <p className="text-xs text-center text-muted-foreground pt-2">
                    We'll keep you updated on our API availability.
                  </p>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </Layout>
  );
} 