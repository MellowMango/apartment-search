import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Layout from '../src/components/Layout';
import { fetchProperties } from '../lib/supabase';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';

export default function HomePage() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);

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
        <div className="relative container mx-auto px-4 py-28 sm:px-6 lg:px-8 flex flex-col items-center">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-center mb-6 leading-tight">
              Austin's Premier <span className="text-secondary">Multifamily</span> Investment Platform
            </h1>
            <p className="text-xl md:text-2xl text-center max-w-3xl mx-auto mb-10 text-primary-foreground/90 leading-relaxed">
              Discover and analyze high-potential multifamily properties across Austin with our interactive map and comprehensive market data.
            </p>
            <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-6">
              <Button asChild size="lg" className="px-8 py-6 text-lg font-semibold shadow-lg hover:shadow-xl transition-all">
                <Link href="/map">Explore Properties</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="bg-transparent text-primary-foreground border-primary-foreground/40 hover:bg-primary-foreground/10 px-8 py-6 text-lg font-semibold">
                <Link href="/signup">Create Free Account</Link>
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
          <h2 className="text-3xl font-bold text-center mb-4">Why Investors Choose Acquire</h2>
          <p className="text-xl text-center text-muted-foreground max-w-3xl mx-auto mb-16">
            Our platform gives you the edge in Austin's competitive multifamily market
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <Card className="bg-background border-none shadow-lg hover:shadow-xl transition-all">
              <CardHeader className="text-center">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-primary">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
                  </svg>
                </div>
                <CardTitle>Market Intelligence</CardTitle>
                <CardDescription className="text-lg">Access comprehensive market data and analytics</CardDescription>
              </CardHeader>
              <CardContent>
                <p>Our platform aggregates data from multiple sources to provide you with the most up-to-date and accurate property information, including cap rates, rental trends, and neighborhood metrics.</p>
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
                <CardDescription className="text-lg">Visualize properties with our intuitive interface</CardDescription>
              </CardHeader>
              <CardContent>
                <p>Easily browse properties by location, filter by your specific criteria, and get a comprehensive view of the Austin multifamily market with our advanced interactive mapping technology.</p>
              </CardContent>
            </Card>
            
            <Card className="bg-background border-none shadow-lg hover:shadow-xl transition-all">
              <CardHeader className="text-center">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-primary">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                  </svg>
                </div>
                <CardTitle>Opportunity Alerts</CardTitle>
                <CardDescription className="text-lg">Never miss a potential investment opportunity</CardDescription>
              </CardHeader>
              <CardContent>
                <p>Our system continuously monitors the market and provides immediate updates when new properties become available or when existing listings change, giving you the edge to act quickly.</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-4">What Our Clients Say</h2>
          <p className="text-lg text-center text-muted-foreground max-w-3xl mx-auto mb-16">
            Join hundreds of investors who've found success with Acquire Apartments
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="bg-muted/30 border border-muted">
              <CardHeader>
                <div className="flex items-center mb-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                </div>
                <div className="font-medium flex items-center">
                  <span className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center mr-2">JS</span>
                  <span>James S.</span>
                </div>
                <CardDescription className="text-sm">Real Estate Investor</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="italic">"Acquire Apartments has completely transformed my investment strategy. I found a 24-unit property that wasn't even on my radar, and closed the deal in record time."</p>
              </CardContent>
            </Card>
            
            <Card className="bg-muted/30 border border-muted">
              <CardHeader>
                <div className="flex items-center mb-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                </div>
                <div className="font-medium flex items-center">
                  <span className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center mr-2">ML</span>
                  <span>Michelle L.</span>
                </div>
                <CardDescription className="text-sm">Property Developer</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="italic">"The data analytics and neighborhood insights have been invaluable for my business. I've been able to identify emerging areas in Austin before they trend."</p>
              </CardContent>
            </Card>
            
            <Card className="bg-muted/30 border border-muted">
              <CardHeader>
                <div className="flex items-center mb-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="text-yellow-500 h-5 w-5">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                </div>
                <div className="font-medium flex items-center">
                  <span className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center mr-2">DP</span>
                  <span>David P.</span>
                </div>
                <CardDescription className="text-sm">Investment Firm Partner</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="italic">"We've added six properties to our portfolio in the last year using Acquire. The real-time alerts and detailed property analysis tools are simply unmatched."</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Enhanced CTA Section */}
      <section className="py-20 bg-primary text-primary-foreground relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/images/pattern.svg')] opacity-10"></div>
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-4xl font-bold mb-6">Ready to find your next investment?</h2>
            <p className="text-xl mb-10 text-primary-foreground/90">
              Join today and get exclusive access to Austin's most promising multifamily properties before they hit the market.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-6">
              <Button asChild size="lg" variant="secondary" className="px-10 py-6 text-lg font-semibold shadow-xl hover:shadow-2xl transition-all">
                <Link href="/signup">Create Free Account</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="bg-transparent text-primary-foreground border-primary-foreground/40 hover:bg-primary-foreground/10 px-10 py-6 text-lg font-semibold">
                <Link href="/map">Browse Properties</Link>
              </Button>
            </div>
            <p className="mt-6 text-primary-foreground/80 text-sm">
              No credit card required. Full access to property listings and market data.
            </p>
          </div>
        </div>
      </section>
    </Layout>
  );
} 