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

  return (
    <Layout title="Acquire Apartments | Austin Multifamily Property Listings">
      {/* Hero Section */}
      <section className="relative bg-primary text-primary-foreground">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/90 to-primary opacity-90"></div>
        <div className="relative container mx-auto px-4 py-24 sm:px-6 lg:px-8 flex flex-col items-center">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-center mb-6">
            Acquire<span className="opacity-80">.</span> Apartments
          </h1>
          <p className="text-xl text-center max-w-3xl mb-10 text-primary-foreground/80">
            Discover and analyze multifamily properties across Austin with our interactive map and comprehensive data.
          </p>
          <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
            <Button asChild size="lg" variant="secondary">
              <Link href="/map">Explore the Map</Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="bg-transparent text-primary-foreground border-primary-foreground/30 hover:bg-primary-foreground/10">
              <Link href="/signup">Create Account</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Why Choose Acquire Apartments</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <CardTitle>Comprehensive Data</CardTitle>
                <CardDescription>Access detailed information on all multifamily properties in Austin</CardDescription>
              </CardHeader>
              <CardContent>
                <p>Our platform aggregates data from multiple sources to provide you with the most up-to-date and accurate property information available.</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Interactive Map</CardTitle>
                <CardDescription>Visualize properties with our intuitive mapping interface</CardDescription>
              </CardHeader>
              <CardContent>
                <p>Easily browse properties by location, filter by your specific criteria, and get a comprehensive view of the Austin multifamily market.</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Real-Time Updates</CardTitle>
                <CardDescription>Stay informed with the latest property listings and changes</CardDescription>
              </CardHeader>
              <CardContent>
                <p>Our system continuously monitors the market and provides immediate updates when new properties become available or existing listings change.</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-muted">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6">Ready to get started?</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto">Create an account today to access all features and start discovering multifamily investment opportunities in Austin.</p>
          <div className="flex justify-center space-x-4">
            <Button asChild size="lg">
              <Link href="/signup">Sign Up Now</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/map">View the Map</Link>
            </Button>
          </div>
        </div>
      </section>
    </Layout>
  );
} 