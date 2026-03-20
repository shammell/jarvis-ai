# ==========================================================
# JARVIS v11.0 GENESIS - Autonomous Economic Agency (AEA)
# JARVIS can spend money, hire humans, and manage budgets
# ==========================================================

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class AutonomousEconomicAgent:
    """
    Autonomous Economic Agency for JARVIS v11.0
    - Crypto wallet integration
    - Stripe virtual card management
    - Budget tracking and limits
    - Autonomous payments
    - Human hiring via Upwork/Fiverr
    """

    def __init__(self, monthly_budget: float = 100.0):
        self.monthly_budget = monthly_budget
        self.spent_this_month = 0.0
        self.transactions = []
        self.virtual_cards = {}
        self.hired_humans = []

        # API keys (from environment)
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        self.upwork_api_key = os.getenv("UPWORK_API_KEY")
        self.crypto_wallet_key = os.getenv("CRYPTO_WALLET_PRIVATE_KEY")

        logger.info(f"💰 Economic Agency initialized with ${monthly_budget}/month budget")

    def check_budget(self, amount: float) -> bool:
        """Check if we have budget for this expense"""
        remaining = self.monthly_budget - self.spent_this_month

        if amount > remaining:
            logger.warning(f"⚠️ Insufficient budget: ${amount} requested, ${remaining} available")
            return False

        return True

    async def create_virtual_card(self, purpose: str, limit: float) -> Dict[str, Any]:
        """
        Create a Stripe virtual card for specific purpose

        Args:
            purpose: What this card is for (e.g., "AWS Services", "Domain Purchase")
            limit: Spending limit for this card

        Returns:
            Card details
        """
        if not self.check_budget(limit):
            return {"success": False, "error": "Budget exceeded"}

        logger.info(f"💳 Creating virtual card for: {purpose} (limit: ${limit})")

        try:
            # TODO: Integrate with Stripe Issuing API
            # For now, simulate card creation
            card = {
                "id": f"card_{hash(purpose + str(datetime.now()))}",
                "purpose": purpose,
                "limit": limit,
                "spent": 0.0,
                "status": "active",
                "created_at": datetime.now().isoformat()
            }

            self.virtual_cards[card["id"]] = card

            logger.info(f"✅ Virtual card created: {card['id']}")

            return {
                "success": True,
                "card": card
            }

        except Exception as e:
            logger.error(f"❌ Card creation failed: {e}")
            return {"success": False, "error": str(e)}

    async def make_payment(
        self,
        amount: float,
        recipient: str,
        purpose: str,
        method: str = "stripe"
    ) -> Dict[str, Any]:
        """
        Make autonomous payment

        Args:
            amount: Amount to pay
            recipient: Who to pay (email, wallet address, etc.)
            purpose: What this payment is for
            method: Payment method (stripe, crypto, paypal)

        Returns:
            Payment result
        """
        if not self.check_budget(amount):
            return {"success": False, "error": "Budget exceeded"}

        logger.info(f"💸 Making payment: ${amount} to {recipient} for {purpose}")

        try:
            # Record transaction
            transaction = {
                "id": f"txn_{hash(str(datetime.now()))}",
                "amount": amount,
                "recipient": recipient,
                "purpose": purpose,
                "method": method,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }

            self.transactions.append(transaction)
            self.spent_this_month += amount

            logger.info(f"✅ Payment completed: {transaction['id']}")
            logger.info(f"📊 Budget: ${self.spent_this_month}/${self.monthly_budget} spent")

            return {
                "success": True,
                "transaction": transaction,
                "remaining_budget": self.monthly_budget - self.spent_this_month
            }

        except Exception as e:
            logger.error(f"❌ Payment failed: {e}")
            return {"success": False, "error": str(e)}

    async def hire_human(
        self,
        task_description: str,
        budget: float,
        platform: str = "upwork",
        skills_required: List[str] = None
    ) -> Dict[str, Any]:
        """
        Hire a human freelancer for tasks JARVIS cannot do

        Args:
            task_description: What needs to be done
            budget: How much to pay
            platform: upwork, fiverr, or freelancer
            skills_required: Required skills

        Returns:
            Hiring result
        """
        if not self.check_budget(budget):
            return {"success": False, "error": "Budget exceeded"}

        logger.info(f"👤 Hiring human for: {task_description[:50]}... (budget: ${budget})")

        try:
            # TODO: Integrate with Upwork/Fiverr API
            # For now, simulate hiring process

            job_posting = {
                "id": f"job_{hash(task_description + str(datetime.now()))}",
                "description": task_description,
                "budget": budget,
                "platform": platform,
                "skills": skills_required or [],
                "status": "posted",
                "posted_at": datetime.now().isoformat()
            }

            self.hired_humans.append(job_posting)

            logger.info(f"✅ Job posted: {job_posting['id']}")

            return {
                "success": True,
                "job": job_posting,
                "message": f"Job posted on {platform}. Waiting for proposals."
            }

        except Exception as e:
            logger.error(f"❌ Hiring failed: {e}")
            return {"success": False, "error": str(e)}

    async def purchase_service(
        self,
        service_name: str,
        provider: str,
        amount: float,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Purchase cloud services, domains, APIs, etc.

        Args:
            service_name: What to buy (e.g., "domain", "aws_ec2", "openai_api")
            provider: Service provider
            amount: Cost
            config: Service configuration

        Returns:
            Purchase result
        """
        if not self.check_budget(amount):
            return {"success": False, "error": "Budget exceeded"}

        logger.info(f"🛒 Purchasing: {service_name} from {provider} (${amount})")

        try:
            # Make payment
            payment = await self.make_payment(
                amount=amount,
                recipient=provider,
                purpose=f"Purchase {service_name}",
                method="stripe"
            )

            if not payment["success"]:
                return payment

            # Record service purchase
            purchase = {
                "id": f"purchase_{hash(service_name + str(datetime.now()))}",
                "service": service_name,
                "provider": provider,
                "amount": amount,
                "config": config or {},
                "transaction_id": payment["transaction"]["id"],
                "status": "active",
                "purchased_at": datetime.now().isoformat()
            }

            logger.info(f"✅ Service purchased: {purchase['id']}")

            return {
                "success": True,
                "purchase": purchase
            }

        except Exception as e:
            logger.error(f"❌ Purchase failed: {e}")
            return {"success": False, "error": str(e)}

    def get_financial_report(self) -> Dict[str, Any]:
        """Get financial summary"""
        return {
            "monthly_budget": self.monthly_budget,
            "spent_this_month": self.spent_this_month,
            "remaining_budget": self.monthly_budget - self.spent_this_month,
            "total_transactions": len(self.transactions),
            "active_cards": len([c for c in self.virtual_cards.values() if c["status"] == "active"]),
            "hired_humans": len(self.hired_humans),
            "recent_transactions": self.transactions[-5:] if self.transactions else []
        }

    def reset_monthly_budget(self):
        """Reset budget at start of new month"""
        logger.info(f"🔄 Resetting monthly budget (spent: ${self.spent_this_month})")
        self.spent_this_month = 0.0
        logger.info(f"✅ Budget reset to ${self.monthly_budget}")

    def save_state(self, filepath: str):
        """Save economic state"""
        data = {
            "monthly_budget": self.monthly_budget,
            "spent_this_month": self.spent_this_month,
            "transactions": self.transactions[-100:],  # Keep last 100
            "virtual_cards": self.virtual_cards,
            "hired_humans": self.hired_humans
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"💾 Economic state saved to {filepath}")

    def load_state(self, filepath: str):
        """Load economic state"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.monthly_budget = data.get("monthly_budget", 100.0)
            self.spent_this_month = data.get("spent_this_month", 0.0)
            self.transactions = data.get("transactions", [])
            self.virtual_cards = data.get("virtual_cards", {})
            self.hired_humans = data.get("hired_humans", [])

            logger.info(f"📂 Economic state loaded from {filepath}")

        except Exception as e:
            logger.error(f"❌ Failed to load state: {e}")


# Test
if __name__ == "__main__":
    import asyncio

    async def test_economic_agency():
        agent = AutonomousEconomicAgent(monthly_budget=100.0)

        print("\n" + "="*50)
        print("AUTONOMOUS ECONOMIC AGENCY TEST")
        print("="*50)

        # Test 1: Create virtual card
        print("\n1. Creating virtual card...")
        card = await agent.create_virtual_card("AWS Services", 50.0)
        print(f"Result: {card}")

        # Test 2: Make payment
        print("\n2. Making payment...")
        payment = await agent.make_payment(
            amount=15.0,
            recipient="namecheap.com",
            purpose="Domain purchase: ai-tees-trend.com"
        )
        print(f"Result: {payment}")

        # Test 3: Purchase service
        print("\n3. Purchasing service...")
        purchase = await agent.purchase_service(
            service_name="domain",
            provider="namecheap",
            amount=12.0,
            config={"domain": "jarvis-ai.com", "years": 1}
        )
        print(f"Result: {purchase}")

        # Test 4: Hire human
        print("\n4. Hiring human freelancer...")
        hire = await agent.hire_human(
            task_description="Design 10 t-shirt graphics with AI theme",
            budget=30.0,
            platform="fiverr",
            skills_required=["graphic design", "AI art"]
        )
        print(f"Result: {hire}")

        # Test 5: Financial report
        print("\n5. Financial Report:")
        report = agent.get_financial_report()
        print(json.dumps(report, indent=2))

    asyncio.run(test_economic_agency())
