# Carrier Operational SLA & Contractual Policies (2026)

## 1. Scope & Validity
- **Effective Period**: July 1, 2026 – September 30, 2026.
- **Coverage**: All delivery routes originating from company hubs and destined for nationwide hubs (including Jakarta, Surabaya, Bandung, Medan, Semarang, and Makassar).
- **Service Categories**:
  - `standard`: Ground freight logistics (estimated SLA 2–5 business days).
  - `express`: Priority air and direct logistics (estimated SLA 24–48 hours).

---

## 2. On-Time Delivery Service Level Agreements (SLA Targets)

| Carrier ID | Carrier Name | Applicable Service Level | Target On-Time Delivery Rate | Grace Period |
| :--- | :--- | :--- | :--- | :--- |
| **C01** | Apex TransLog / C01 Logistics | All (Standard & Express) | **≥ 95.0%** | 0 minutes |
| **C02** | Nusantara Express / C02 Freight | Express | **≥ 90.0%** | 0 minutes |
| **C02** | Nusantara Express / C02 Freight | Standard | **≥ 85.0%** | 0 minutes |
| **C03** | SwiftKilat / C03 Courier | Express | **≥ 93.0%** | 0 minutes |

### Calculation Standard
- **On-Time Rate**: Formally defined as `on_time_delivered_count / delivered_count`.
- Packages still marked as `in_transit` are strictly excluded from the late denominator until actual arrival (`delivered_at_utc`).

---

## 3. Financial Penalties, Liquidated Damages & Refund Policy

### Clause 3.1: Express Late Delivery Refund (100% Reimbursement)
- Any parcel shipped under the `express` service level whose `delivered_at_utc > promised_delivery_at_utc` automatically entitles the shipper to a **100% full shipping fee refund** (`refund_amount_idr = shipping_fee_idr`).
- *Operational Context*: Because Express shipping fees are significantly higher than Standard fees, late express deliveries generate a disproportionate impact on the total financial `refund_rate` (`SUM(refund_amount_idr) / SUM(shipping_fee_idr)`).

### Clause 3.2: Standard Late Delivery Refund (50% Reimbursement)
- Any parcel shipped under the `standard` service level whose `delivered_at_utc > promised_delivery_at_utc` is eligible for a **50% partial refund** of the shipping fee, provided the delay exceeds 24 hours past the promised window.

### Clause 3.3: In-Transit & Lost Package Provisions
- Packages in `in_transit` status are not classified as late for refund settlement until either delivered or declared lost after 14 calendar days without a checkpoint scan.

---

## 4. Contractual Review & Sanctions
- **Monthly SLA Audit**: Conducted on the 1st of every month.
- **Carrier Sanction**: Any carrier failing to meet their minimum agreed on-time target over a 30-day window is subject to a 5% contractual penalty deducted from monthly freight payouts, and routing volume allocation will be reduced by 20% in subsequent cycles.
