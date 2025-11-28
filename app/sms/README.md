# SMS Alarm Integration Module

This module handles incoming SMS alarms via SMS gateway webhook integration.

## Structure

- **`parser.py`** - Parses SMS content to detect departments and extract alarm details
- **`handler.py`** - Creates database records from parsed SMS data
- **`webhook.py`** - Flask routes for receiving SMS webhooks
- **`config.py`** - Configuration for department patterns and settings

## Usage

### Webhook Endpoints

- **`POST /sms-webhook`** - Main webhook endpoint for SMS gateway
- **`GET /sms-webhook`** - Alternative GET endpoint (for testing)
- **`POST /sms-test`** - Test endpoint that parses without creating database records

### SMS Message Format

The system expects SMS messages in this format:

```text
[codes], [department]_[type]_[description]
```

Examples:

- `A01, DEPT01_C_440_Type of reinforcement Fire Department` → Station A alarm
- `B01, B02, B03, A01, A02, A03, POLICE, PoliceTech_A_422_Class: Major Alarm - Building Fire` → Station B alarm

### Department Detection

The system detects departments based on patterns configured in `config.py`. Configure your department patterns to match your SMS message format:

- **Station A (DEPT01)**: `A01`, `A02`, `A03`, `DEPT01`, `Station A`
- **Station B (DEPT02)**: `B01`, `B02`, `B03`, `DEPT02`, `Station B`
- **Station C (DEPT03)**: `C01`, `C02`, `C03`, `DEPT03`, `Station C`
- **Station D (DEPT04)**: `D01`, `D02`, `D03`, `DEPT04`, `Station D`
- **Station E (DEPT05)**: `E01`, `E02`, `E03`, `DEPT05`, `Station E`

### Alarm Types

- **Real**: Default for actual emergencies
- **Practice**: Messages containing `PROVALARM`, `Övning`
- **Test**: Messages containing `test`, `TEST`

## Configuration

Edit `config.py` to modify:

- Department detection patterns (customize for your departments)
- Alarm type patterns
- Webhook settings
- SMS gateway integration settings

## Testing

Use the provided `test_sms_integration.py` script to test the integration:

```bash
python test_sms_integration.py
```

This will test both the parser (no database changes) and webhook (creates alarms) endpoints.

## SMS Gateway Setup

1. Configure webhook URL in your SMS gateway: `https://yourdomain.com/sms-webhook`
2. Set method to POST (recommended) or GET
3. Set content type to `application/json` for POST
4. The system will automatically process incoming SMS and create alarm records
5. Customize department patterns in `config.py` to match your SMS message format
