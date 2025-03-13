# Data Model Diagram

This file contains a text-based diagram of the data model for the Austin Multifamily Property Listing Map application.

## Entity Relationship Diagram (Supabase/PostgreSQL)

```
+----------------+       +----------------+       +----------------+
|   Properties   |       |    Brokers     |       |   Brokerages   |
+----------------+       +----------------+       +----------------+
| id             |<----->| id             |<----->| id             |
| name           |       | name           |       | name           |
| address        |       | company        |       | website        |
| city           |       | email          |       | logo_url       |
| state          |       | phone          |       | address        |
| zip_code       |       | website        |       | city           |
| latitude       |       | brokerage_id   |       | state          |
| longitude      |       | created_at     |       | zip_code       |
| price          |       | updated_at     |       | created_at     |
| units          |       +----------------+       | updated_at     |
| year_built     |                                +----------------+
| year_renovated |                                        ^
| square_feet    |                                        |
| price_per_unit |       +----------------+               |
| price_per_sqft |       | User Profiles  |               |
| cap_rate       |       +----------------+               |
| property_type  |       | id             |               |
| property_status|       | email          |               |
| property_website|      | first_name     |               |
| listing_website|       | last_name      |               |
| call_for_offers|       | company        |               |
| description    |       | phone          |               |
| amenities      |       | role           |               |
| images         |       | is_active      |               |
| broker_id      |------>| subscription_id|               |
| brokerage_id   |------>| created_at     |               |
| created_at     |       | updated_at     |               |
| updated_at     |       +----------------+               |
| date_first_app.|               ^                        |
+----------------+               |                        |
        ^                        |                        |
        |                        |                        |
        |                +----------------+       +----------------+
        |                | Subscriptions  |       | Saved Props    |
        |                +----------------+       +----------------+
        |                | id             |       | id             |
        |                | user_id        |------>| user_id        |
        |                | stripe_cust_id |       | property_id    |----+
        |                | stripe_sub_id  |       | created_at     |    |
        |                | plan_type      |       +----------------+    |
        |                | status         |                             |
        |                | period_start   |       +----------------+    |
        |                | period_end     |       | Property Notes |    |
        |                | created_at     |       +----------------+    |
        |                | updated_at     |       | id             |    |
        |                +----------------+       | user_id        |    |
        |                                         | property_id    |----+
        |                                         | content        |
        |                                         | created_at     |
        |                                         | updated_at     |
        |                                         +----------------+
        |
        +
```

## Graph Model (Neo4j)

```
                  +----------------+
                  |   Brokerage    |
                  +----------------+
                  | id             |
                  | name           |
                  | website        |
                  | city           |
                  | state          |
                  +----------------+
                    ^            |
                    |            |
                    |            |
BELONGS_TO          |            | REPRESENTS
                    |            |
                    |            v
+----------------+  |  +----------------+
|     Broker     |  |  |    Property    |
+----------------+  |  +----------------+
| id             |  |  | id             |
| name           |  |  | name           |
| company        |  |  | address        |
| email          |  |  | city           |
| phone          |  |  | state          |
| website        |  |  | zip_code       |
+----------------+  |  | latitude       |
      |             |  | longitude      |
      |             |  | price          |
      |             |  | units          |
      |             |  | year_built     |
      |             |  | square_feet    |
      |             |  | price_per_unit |
      |             |  | property_type  |
      |             |  | property_status|
      |             |  +----------------+
      |             |        |     |
      |             |        |     |
      |             |        |     |
LISTS |             |        |     | SIMILAR_TO
      |             |        |     |
      |             |        |     |
      v             |        v     v
+----------------+  |  +----------------+
|    Property    |<-+  |    Property    |
+----------------+     +----------------+
                            ^     |
                            |     |
                            |     |
                         NEAR     |
                            |     |
                            |     v
                       +----------------+
                       |    Property    |
                       +----------------+
```

## Relationship Types in Neo4j

1. **LISTS**: Broker lists Property
   - Direction: Broker -> Property
   - Properties: None

2. **BELONGS_TO**: Broker belongs to Brokerage
   - Direction: Broker -> Brokerage
   - Properties: None

3. **REPRESENTS**: Brokerage represents Property
   - Direction: Brokerage -> Property
   - Properties: None

4. **WORKS_WITH**: Broker works with Broker
   - Direction: Broker -> Broker
   - Properties: 
     - shared_properties: Number of properties they both work with

5. **NEAR**: Property is near Property
   - Direction: Property -> Property
   - Properties:
     - distance: Distance in meters between properties

6. **SIMILAR_TO**: Property is similar to Property
   - Direction: Property -> Property
   - Properties:
     - price_diff: Percentage difference in price
     - units_diff: Percentage difference in units

7. **COMPETES_WITH**: Brokerage competes with Brokerage
   - Direction: Brokerage -> Brokerage
   - Properties:
     - area_overlap: Number of areas where both have properties
``` 