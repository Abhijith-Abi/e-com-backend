# Production Deployment Steps - Fix Product Migration Error

## Problem
Production server error: `table products_product has no column named redeem_points`

**Root Cause**: Production database still has the old `redeem_points` column, but the code expects the new schema with `required_points` field and no `redeem_points` field.

## Solution
Run the pending migrations on production server.

---

## Step-by-Step Instructions

### Option 1: Using the Automated Script (Recommended)

1. **Upload the deployment script to production server:**
   ```bash
   scp deploy_migrations.sh user@api.iqraamark.com:/var/www/house-of-vaz/house-of-vaz-backend-system/
   ```

2. **SSH into production server:**
   ```bash
   ssh user@api.iqraamark.com
   ```

3. **Navigate to project directory:**
   ```bash
   cd /var/www/house-of-vaz/house-of-vaz-backend-system
   ```

4. **Make script executable and run it:**
   ```bash
   chmod +x deploy_migrations.sh
   ./deploy_migrations.sh
   ```

---

### Option 2: Manual Step-by-Step (If script doesn't work)

1. **SSH into production server:**
   ```bash
   ssh user@api.iqraamark.com
   ```

2. **Navigate to project directory:**
   ```bash
   cd /var/www/house-of-vaz/house-of-vaz-backend-system
   ```

3. **Create database backup (IMPORTANT!):**
   ```bash
   cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
   ```

4. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

5. **Check current migration status:**
   ```bash
   python manage.py showmigrations products
   ```
   
   You should see something like:
   ```
   products
    [X] 0001_initial
    [ ] 0002_product_earn_points
    [ ] 0003_rename_earn_points_to_required_points
    [ ] 0004_remove_redeem_points
   ```

6. **Upload migration files (if not using git):**
   
   If you're NOT using git to deploy, you need to manually copy these migration files to production:
   - `apps/products/migrations/0002_product_earn_points.py`
   - `apps/products/migrations/0003_rename_earn_points_to_required_points.py`
   - `apps/products/migrations/0004_remove_redeem_points.py`
   
   Use SCP or FTP to upload them to:
   `/var/www/house-of-vaz/house-of-vaz-backend-system/apps/products/migrations/`

7. **OR pull latest code (if using git):**
   ```bash
   git pull origin main
   ```

8. **Run migrations:**
   ```bash
   python manage.py migrate products
   ```
   
   Expected output:
   ```
   Running migrations:
     Applying products.0002_product_earn_points... OK
     Applying products.0003_rename_earn_points_to_required_points... OK
     Applying products.0004_remove_redeem_points... OK
   ```

9. **Restart gunicorn:**
   ```bash
   sudo systemctl restart gunicorn
   ```

10. **Check gunicorn status:**
    ```bash
    sudo systemctl status gunicorn
    ```
    
    Should show "active (running)"

11. **Test the API:**
    Try creating a product again through the API:
    ```
    POST https://api.iqraamark.com/api/v1/warehouses/{warehouse_id}/products/
    ```

---

## What These Migrations Do

1. **Migration 0002**: Adds `earn_points` field (temporary)
2. **Migration 0003**: 
   - Removes `earn_points` field
   - Adds `required_points` field
   - Modifies `redeem_points` field (makes it nullable)
3. **Migration 0004**: Removes `redeem_points` field completely

**Final Result**: Product model will have only `required_points` field (no `redeem_points`, no `earn_points`)

---

## Verification

After deployment, verify the changes:

1. **Check database schema:**
   ```bash
   python manage.py dbshell
   ```
   
   Then in SQLite:
   ```sql
   .schema products_product
   ```
   
   You should see `required_points` field but NO `redeem_points` field.

2. **Test product creation:**
   - Create a product with `required_points` value
   - Verify it saves successfully
   - Check the response includes `required_points`

3. **Test cart/checkout:**
   - Add product to cart
   - Verify `total_required_points` is calculated correctly
   - Test checkout flow

---

## Rollback (If Something Goes Wrong)

If the migration causes issues:

1. **Restore database backup:**
   ```bash
   cd /var/www/house-of-vaz/house-of-vaz-backend-system
   cp db.sqlite3.backup.YYYYMMDD_HHMMSS db.sqlite3
   ```
   (Replace YYYYMMDD_HHMMSS with your backup timestamp)

2. **Restart gunicorn:**
   ```bash
   sudo systemctl restart gunicorn
   ```

3. **Contact developer for assistance**

---

## Important Notes

- ⚠️ **ALWAYS backup database before running migrations**
- ⚠️ SQLite doesn't support all migration operations - if you encounter issues, you may need to export data, recreate database, and import data
- ⚠️ Consider migrating to PostgreSQL for production (SQLite is not recommended for production)
- ✅ These migrations are safe - they only modify the Product model schema
- ✅ Existing product data will be preserved (only schema changes)

---

## Need Help?

If you encounter any errors during deployment:

1. Check gunicorn logs:
   ```bash
   sudo journalctl -u gunicorn -n 50
   ```

2. Check Django logs (if configured)

3. Share the error message for assistance
