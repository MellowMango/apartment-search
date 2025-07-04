# 🧠 LLM Caching System Guide

## 🎯 **Overview**

The LLM caching system ensures that **each university/department combination is only analyzed once** by the OpenAI API, providing massive cost savings for repeated scraping operations.

## 💰 **Cost Savings**

- **First Discovery**: ~$0.0002 per university/department
- **Subsequent Scrapes**: $0.0000 (uses cache)
- **Cache Duration**: 24 hours (configurable)
- **Storage**: Local JSON files in `cache/llm_discoveries/`

## 🔄 **How It Works**

### 1. **Cache Key Generation**
```
University: "Stanford University" 
Department: "Computer Science"
→ Cache Key: "stanford_university_computer_science"

University: "MIT"
Department: None (general)  
→ Cache Key: "mit_general"
```

### 2. **Discovery Flow**
```
🔍 New University/Department Request
    ↓
📂 Check Cache (cache/llm_discoveries/[key].json)
    ↓
🎯 Cache Hit? → ✅ Return Cached Result ($0.00)
    ↓
🤖 Cache Miss? → Call OpenAI API (~$0.0002)
    ↓
💾 Save Result to Cache
    ↓
📊 Return Discovery Result
```

### 3. **Cache Structure**
Each cached discovery contains:
```json
{
  "faculty_directory_paths": ["faculty", "people", "directory"],
  "department_paths": ["departments/cs"],
  "confidence_score": 0.85,
  "reasoning": "Found clear navigation...",
  "cost_estimate": 0.0002,
  "cached": false,
  "discovery_timestamp": 1640995200.0
}
```

## 🛠️ **Usage Examples**

### **Basic University Discovery**
```python
from lynnapse.core.llm_assistant import LLMUniversityAssistant

assistant = LLMUniversityAssistant()

# First call - uses LLM ($0.0002)
result1 = await assistant.discover_faculty_directories(
    university_name="University of Vermont",
    base_url="https://www.uvm.edu"
)

# Second call - uses cache ($0.0000)
result2 = await assistant.discover_faculty_directories(
    university_name="University of Vermont", 
    base_url="https://www.uvm.edu"
)
```

### **Department-Specific Discovery**
```python
# Psychology department - separate cache entry
psych_result = await assistant.discover_faculty_directories(
    university_name="University of Vermont",
    base_url="https://www.uvm.edu",
    department_name="Psychology"
)

# Computer Science department - another cache entry  
cs_result = await assistant.discover_faculty_directories(
    university_name="University of Vermont",
    base_url="https://www.uvm.edu",
    department_name="Computer Science"
)
```

## 📊 **Cache Management**

### **View Cache Summary**
```bash
python3 lynnapse/cli/cache_manager.py summary
```
Output:
```
📊 CACHE SUMMARY
Total cached discoveries: 5
Total LLM cost saved: $0.0010
Fresh (< 24h): 5
Old (>= 24h): 0
```

### **List All Cached Discoveries**
```bash
python3 lynnapse/cli/cache_manager.py list
```

### **Clean Expired Cache (>24h)**
```bash
python3 lynnapse/cli/cache_manager.py clean
```

### **Clean All Cache**
```bash
python3 lynnapse/cli/cache_manager.py clean-all
```

## 💡 **Best Practices**

### **Cost Optimization**
1. **Test with small universities first** (like University of Vermont)
2. **Use department-specific discovery** when needed
3. **Monitor costs** with `assistant.get_cost_summary()`
4. **Cache persists across sessions** - no repeated costs

### **Cache Management**
1. **Cache expires after 24 hours** (configurable in settings)
2. **Manual cleanup** available via cache manager
3. **Cache files are human-readable JSON**
4. **Safe to delete cache directory** to start fresh

### **Production Usage**
```python
# Check if result was cached
if result.cached:
    print("Used cache - no API cost!")
else:
    print(f"New discovery - cost: ${result.cost_estimate:.4f}")

# Track total costs
cost_summary = assistant.get_cost_summary()
print(f"Total spent: ${cost_summary['total_cost']:.4f}")
print(f"Cached discoveries: {cost_summary['cached_discoveries']}")
```

## 🔧 **Configuration**

In your `.env` file:
```bash
# LLM Configuration
LLM_CACHE_ENABLED=true
LLM_CACHE_TTL=86400        # 24 hours in seconds
LLM_MAX_RETRIES=3
LLM_COST_TRACKING=true

# OpenAI Configuration  
OPENAI_MODEL=gpt-4o-mini   # Cheapest model
OPENAI_MAX_TOKENS=1000     # Keep tokens low
OPENAI_TEMPERATURE=0.1     # Consistent results
```

## 🎯 **Expected Costs**

For a **100-university dataset**:
- **First run**: ~$0.02 (100 × $0.0002)
- **Subsequent runs**: $0.00 (all cached)
- **Department-specific**: +$0.0002 per new dept
- **Total budget**: Well under $20 target

## 🚀 **Integration with UniversityAdapter**

The caching system is automatically integrated into the `UniversityAdapter`:

```python
from lynnapse.core.university_adapter import UniversityAdapter

adapter = UniversityAdapter()

# Uses LLM as 5th fallback strategy with automatic caching
pattern = await adapter.discover_university_structure("New University")

# Check LLM usage
cost_summary = adapter.get_llm_cost_summary()
if cost_summary:
    print(f"LLM costs: ${cost_summary['total_cost']:.4f}")
```

The LLM will only be called when:
1. Traditional methods fail (sitemap, navigation, common paths, subdomain)
2. No cached result exists for the university/department
3. Cached result has expired (>24h)

This ensures **maximum cost efficiency** while maintaining **full dynamic capability**! 