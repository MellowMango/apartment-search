-- Create the property_research table
CREATE TABLE IF NOT EXISTS public.property_research (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    property_id TEXT NOT NULL,
    research_depth TEXT DEFAULT 'basic' CHECK (research_depth IN ('basic', 'standard', 'comprehensive', 'exhaustive')),
    research_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
    executive_summary TEXT,
    modules JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_property_research_property_id ON public.property_research(property_id);
CREATE INDEX IF NOT EXISTS idx_property_research_research_depth ON public.property_research(research_depth);

-- Enable row-level security 
ALTER TABLE public.property_research ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Anyone can view property research" 
ON public.property_research FOR SELECT USING (true);

CREATE POLICY "Authenticated users can edit property research" 
ON public.property_research FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can insert property research" 
ON public.property_research FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Create necessary Celery tables
CREATE TABLE IF NOT EXISTS celery_taskmeta (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(155) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL,
    result JSONB NULL,
    date_done TIMESTAMP WITH TIME ZONE NULL,
    traceback TEXT NULL,
    name VARCHAR(155) NULL,
    args JSONB NULL,
    kwargs JSONB NULL,
    worker VARCHAR(155) NULL,
    retries INTEGER DEFAULT 0,
    queue VARCHAR(155) NULL
);

CREATE TABLE IF NOT EXISTS celery_tasksetmeta (
    id SERIAL PRIMARY KEY,
    taskset_id VARCHAR(155) UNIQUE NOT NULL,
    result JSONB NOT NULL,
    date_done TIMESTAMP WITH TIME ZONE NOT NULL
); 