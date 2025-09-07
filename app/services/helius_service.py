# # app/services/helius_service.py
# import httpx
# import logging
# from typing import List, Dict, Any
# from datetime import datetime, timedelta
# from collections import defaultdict
# from app.core.config import settings


# SOL_MINT = "So11111111111111111111111111111111111111112"

# # Common stablecoins and "buying power" tokens
# STABLECOIN_MINTS = {
#     "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
#     "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",   # USDT
#     "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",   # USDC (Circle)
#     "A9mUU4qviSctJVPJdBJWkb28deg915LYJKrzQ19ji3FM",   # USTv2
#     "Gz7VkD4MacbEB6yC5XD3HcumEiYx2EtDYYrfikGsvopG",   # wsUSDC
# }

# # Tokens that represent "buying power" (SOL + stablecoins)
# BUYING_POWER_TOKENS = {SOL_MINT} | STABLECOIN_MINTS
# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class HeliusService:
#     def __init__(self):
#         self.api_key = settings.HELIUS_API_KEY
#         self.base_url = settings.HELIUS_BASE_URL
    
#     async def get_raw_transactions(self, wallet_address: str, limit: int = 100) -> List[Dict[str, Any]]:
#         """
#         Calls the Helius API to get parsed transactions for a wallet address.
        
#         Args:
#             wallet_address (str): Solana wallet address
#             limit (int): Number of transactions to fetch (max 1000)

#         Returns:
#             List[Dict[str, Any]]: List of decoded transaction data
#         """
#         url = f"{self.base_url}/addresses/{wallet_address}/transactions"
#         params = {
#             "api-key": self.api_key,
#             "limit": limit
#         }

#         try:
#             async with httpx.AsyncClient() as client:
#                 logger.info(f"Making request to: {url}")
#                 logger.info(f"With params: {params}")
#                 response = await client.get(url, params=params)
#                 response.raise_for_status()
#                 data = response.json()
#                 logger.info(f"Successfully fetched {len(data)} transactions for wallet {wallet_address}")
#                 # Helius might return data in a nested structure
#                 if isinstance(data, dict) and "result" in data:
#                     return data["result"]
#                 return data
#         except httpx.HTTPStatusError as http_err:
#             logger.error(f"HTTP error: {http_err.response.status_code} - {http_err.response.text}")
#             raise
#         except Exception as e:
#             logger.error(f"Failed to fetch transactions: {str(e)}")
#             raise

#         return []



#     def detect_wallet_clusters(
#         self,
#         transactions: List[Dict[str, Any]],
#         min_children: int = 5,
#         funding_window_minutes: int = 5
#     ) -> Dict[str, Any]:
#         """
#         Detect wallet clusters where a parent wallet funds multiple child wallets
#         within a short time window, indicating coordinated trading operations.
        
#         Args:
#             transactions: List of transaction data from Helius
#             min_children: Minimum number of children required to form a cluster (default: 5)
#             funding_window_minutes: Time window for cluster formation (default: 5 minutes)
            
#         Returns:
#             Dict containing detected clusters and statistics
#         """
#         # Step 1: Extract all funding events
#         logger.info("Extracting funding events from transactions...")
#         funding_events = []
        
#         for txn in transactions:
#             timestamp = datetime.fromtimestamp(txn["timestamp"])
            
#             # Extract token transfers (includes SOL transfers)
#             for transfer in txn.get("tokenTransfers", []):
#                 from_wallet = transfer.get("fromUserAccount")
#                 to_wallet = transfer.get("toUserAccount")
#                 amount = float(transfer.get("tokenAmount", 0))
#                 mint = transfer.get("mint")
                
#                 if from_wallet and to_wallet and from_wallet != to_wallet and amount > 0:
#                     funding_events.append({
#                         "parent": from_wallet,
#                         "child": to_wallet,
#                         "mint": mint,
#                         "amount": amount,
#                         "timestamp": timestamp,
#                         "signature": txn.get("signature")
#                     })
        
#         # Step 2: Extract all swap events
#         logger.info("Extracting swap events from transactions...")
#         swap_events = {}  # wallet -> swap_info
        
#         for txn in transactions:
#             if txn.get("type") == "SWAP":
#                 timestamp = datetime.fromtimestamp(txn["timestamp"])
#                 fee_payer = txn.get("feePayer")
                
#                 if fee_payer and "events" in txn and "swap" in txn["events"]:
#                     swap_data = txn["events"]["swap"]
                    
#                     # Extract input tokens (what was put into the swap)
#                     input_mints = []
#                     input_amounts = []
#                     for token_input in swap_data.get("tokenInputs", []):
#                         if token_input.get("userAccount") == fee_payer:
#                             input_mints.append(token_input.get("mint"))
#                             raw_amount = token_input.get("rawTokenAmount", {})
#                             amount = float(raw_amount.get("tokenAmount", 0))
#                             decimals = raw_amount.get("decimals", 0)
#                             input_amounts.append(amount / (10 ** decimals))
                    
#                     # Extract output tokens (what came out of the swap)
#                     output_mints = []
#                     for inner_swap in swap_data.get("innerSwaps", []):
#                         for token_output in inner_swap.get("tokenOutputs", []):
#                             if token_output.get("toUserAccount") == fee_payer:
#                                 output_mints.append(token_output.get("mint"))
                    
#                     swap_events[fee_payer] = {
#                         "timestamp": timestamp,
#                         "input_mints": input_mints,
#                         "output_mints": output_mints,
#                         "input_amounts": input_amounts,
#                         "signature": txn.get("signature")
#                     }
        
#         # Step 3: Find funding clusters
#         logger.info("Detecting funding clusters...")
#         clusters = []
#         parent_funding_groups = defaultdict(list)
        
#         # Group funding events by parent
#         for event in funding_events:
#             parent_funding_groups[event["parent"]].append(event)
        
#         # Check each parent for cluster formation
#         for parent, parent_events in parent_funding_groups.items():
#             # Sort events by timestamp
#             sorted_events = sorted(parent_events, key=lambda x: x["timestamp"])
            
#             # Use sliding window to find clusters
#             for i in range(len(sorted_events)):
#                 window_start = sorted_events[i]["timestamp"]
#                 window_end = window_start + timedelta(minutes=funding_window_minutes)
                
#                 # Find all events within this window
#                 window_events = []
#                 for j in range(i, len(sorted_events)):
#                     if sorted_events[j]["timestamp"] <= window_end:
#                         window_events.append(sorted_events[j])
#                     else:
#                         break
                
#                 # Check if we have enough children for a cluster
#                 unique_children = list(set(event["child"] for event in window_events))
#                 if len(unique_children) >= min_children:
                    
#                     # Analyze cluster
#                     cluster = self._analyze_cluster(
#                         parent, 
#                         window_events, 
#                         unique_children, 
#                         swap_events, 
#                         window_start, 
#                         window_end
#                     )
                    
#                     clusters.append(cluster)
#                     break  # Found a cluster for this parent, move to next parent
        
#         logger.info(f"Found {len(clusters)} wallet clusters")
        
#         return {
#             "detection_params": {
#                 "min_children": min_children,
#                 "funding_window_minutes": funding_window_minutes,
#                 "total_transactions_analyzed": len(transactions)
#             },
#             "summary": {
#                 "clusters_found": len(clusters),
#                 "total_parents": len([c for c in clusters]),
#                 "total_children": sum(c["funding_stats"]["children_funded"] for c in clusters),
#                 "total_children_swapped": sum(c["swap_stats"]["children_swapped"] for c in clusters)
#             },
#             "clusters": clusters
#         }
    
#     def _analyze_cluster(
#         self, 
#         parent: str, 
#         funding_events: List[Dict], 
#         children: List[str], 
#         swap_events: Dict, 
#         window_start: datetime, 
#         window_end: datetime
#     ) -> Dict[str, Any]:
#         """
#         Analyze a detected cluster to extract detailed statistics.
#         """
#         # Calculate funding statistics
#         total_funding = sum(event["amount"] for event in funding_events)
#         funding_token = funding_events[0]["mint"]  # Assume same token for cluster
        
#         # Check children swap behavior
#         children_data = []
#         children_swapped = 0
#         total_swap_amount = 0
#         target_tokens = set()
        
#         for child in children:
#             child_funding_events = [e for e in funding_events if e["child"] == child]
#             child_funding_amount = sum(e["amount"] for e in child_funding_events)
            
#             child_info = {
#                 "wallet": child,
#                 "funded_amount": child_funding_amount,
#                 "swap_status": "pending",
#                 "swap_amount": 0,
#                 "swap_time": None,
#                 "target_tokens": []
#             }
            
#             # Check if child has swapped
#             if child in swap_events:
#                 swap = swap_events[child]
#                 # Check if child used the funded token in swap
#                 if funding_token in swap["input_mints"]:
#                     child_info["swap_status"] = "completed"
                    
#                     # Find the amount of funded token used
#                     for i, mint in enumerate(swap["input_mints"]):
#                         if mint == funding_token and i < len(swap["input_amounts"]):
#                             child_info["swap_amount"] = swap["input_amounts"][i]
#                             total_swap_amount += swap["input_amounts"][i]
#                             break
                    
#                     child_info["swap_time"] = swap["timestamp"].isoformat()
#                     child_info["target_tokens"] = swap["output_mints"]
#                     children_swapped += 1
#                     target_tokens.update(swap["output_mints"])
            
#             children_data.append(child_info)
        
#         # Determine cluster type based on funding token
#         if funding_token in BUYING_POWER_TOKENS:
#             cluster_type = "BUY_CLUSTER"  # SOL or stablecoin funding = buying power
#         else:
#             cluster_type = "SELL_CLUSTER"  # Specific token funding = likely for selling
        
#         return {
#             "cluster_id": f"{parent}_{int(window_start.timestamp())}",
#             "parent_wallet": parent,
#             "formation_time": window_start.isoformat(),
#             "formation_window": f"{window_start.isoformat()} - {window_end.isoformat()}",
#             "cluster_type": cluster_type,
            
#             "funding_stats": {
#                 "children_funded": len(children),
#                 "total_amount_sent": round(total_funding, 6),
#                 "funding_token": funding_token,
#                 "funding_token_symbol": self._get_token_symbol(funding_token)
#             },
            
#             "swap_stats": {
#                 "children_swapped": children_swapped,
#                 "children_pending": len(children) - children_swapped,
#                 "total_amount_swapped": round(total_swap_amount, 6),
#                 "swap_completion_rate": f"{(children_swapped/len(children)*100):.1f}%",
#                 "target_tokens": list(target_tokens),
#                 "coordinated_target": len(target_tokens) == 1  # True if all target same token
#             },
            
#             "children": children_data
#         }
    
#     def _get_token_symbol(self, mint: str) -> str:
#         """
#         Get the human-readable symbol for a token mint address.
#         """
#         token_symbols = {
#             "So11111111111111111111111111111111111111112": "SOL",
#             "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
#             "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
#             "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU": "USDC",
#             "A9mUU4qviSctJVPJdBJWkb28deg915LYJKrzQ19ji3FM": "USTv2",
#             "Gz7VkD4MacbEB6yC5XD3HcumEiYx2EtDYYrfikGsvopG": "wsUSDC"
#         }
#         return token_symbols.get(mint, "TOKEN")  





# Sohail code here

# # app/services/helius_service.py
# import httpx
# import logging
# from typing import List, Dict, Any
# from datetime import datetime, timedelta
# from collections import defaultdict
# from app.core.config import settings

# SOL_MINT = "So11111111111111111111111111111111111111112"

# # Common stablecoins and "buying power" tokens
# STABLECOIN_MINTS = {
#     "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
#     "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
#     "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",  # USDC (Circle)
#     "A9mUU4qviSctJVPJdBJWkb28deg915LYJKrzQ19ji3FM",  # USTv2
#     "Gz7VkD4MacbEB6yC5XD3HcumEiYx2EtDYYrfikGsvopG",  # wsUSDC
# }

# # Tokens that represent "buying power" (SOL + stablecoins)
# BUYING_POWER_TOKENS = {SOL_MINT} | STABLECOIN_MINTS

# # Logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class HeliusService:
#     def __init__(self):
#         self.api_key = settings.HELIUS_API_KEY
#         self.base_url = settings.HELIUS_BASE_URL.rstrip("/")
#         self.url_template = settings.HELIUS_TRANSACTIONS_URL

#     async def get_raw_transactions(self, wallet_address: str) -> List[Dict[str, Any]]:
#         """
#         Fetch parsed transactions for a wallet. We DON'T send a 'limit' param here
#         because this Helius endpoint rejects unknown params.
#         """
#         if self.url_template:
#             url = self.url_template.format(address=wallet_address, api_key=self.api_key)
#         else:
#             url = f"{self.base_url}/addresses/{wallet_address}/transactions?api-key={self.api_key}"

#         try:
#             async with httpx.AsyncClient(timeout=30) as client:
#                 logger.info(f"Helius GET {url}")
#                 resp = await client.get(url)
#                 resp.raise_for_status()
#                 data = resp.json()
#                 # Some responses may come wrapped
#                 if isinstance(data, dict) and "result" in data:
#                     return data["result"]
#                 return data if isinstance(data, list) else []
#         except httpx.HTTPStatusError as http_err:
#             logger.error(
#                 f"HTTP error from Helius: {http_err.response.status_code} - {http_err.response.text}"
#             )
#             raise
#         except Exception as e:
#             logger.error(f"Failed to fetch transactions: {e}")
#             raise

#     def detect_wallet_clusters(
#         self,
#         transactions: List[Dict[str, Any]],
#         min_children: int = 5,
#         funding_window_minutes: int = 5,
#     ) -> Dict[str, Any]:
#         """
#         Detect wallet clusters where a parent funds multiple children in a short window.
#         We only count **real funding**:
#           - Native SOL transfers (nativeTransfers)
#           - wSOL token transfers (SOL mint)
#         And we **ignore SWAP transactions** as funding sources.
#         """
#         logger.info("Extracting funding events from transactions...")
#         funding_events: List[Dict[str, Any]] = []

#         for txn in transactions:
#             ts = datetime.fromtimestamp(txn.get("timestamp", 0) or 0)

#             # 1) Ignore SWAP txns for funding detection (they create many program-owned hops)
#             if (txn.get("type") or "").upper() == "SWAP":
#                 continue

#             # 2) Native SOL transfers (lamports)
#             for nt in txn.get("nativeTransfers", []) or []:
#                 from_wallet = nt.get("fromUserAccount") or nt.get("fromUser")
#                 to_wallet = nt.get("toUserAccount") or nt.get("toUser")
#                 lamports = nt.get("amount")  # Helius returns lamports here
#                 try:
#                     amount_sol = float(lamports) / 1_000_000_000 if lamports is not None else 0.0
#                 except Exception:
#                     amount_sol = 0.0

#                 if (
#                     from_wallet
#                     and to_wallet
#                     and from_wallet != to_wallet
#                     and amount_sol > 0
#                 ):
#                     funding_events.append(
#                         {
#                             "parent": from_wallet,
#                             "child": to_wallet,
#                             "mint": SOL_MINT,
#                             "amount": amount_sol,
#                             "timestamp": ts,
#                             "signature": txn.get("signature"),
#                         }
#                     )

#             # 3) wSOL transfers (tokenTransfers with SOL mint)
#             for t in txn.get("tokenTransfers", []) or []:
#                 mint = t.get("mint")
#                 if mint != SOL_MINT:
#                     continue  # only count wSOL as "funding"

#                 from_wallet = t.get("fromUserAccount")
#                 to_wallet = t.get("toUserAccount")
#                 amount = 0.0
#                 if "tokenAmount" in t:
#                     # Some older payloads use 'tokenAmount' (already decimalized)
#                     try:
#                         amount = float(t.get("tokenAmount", 0))
#                     except Exception:
#                         amount = 0.0
#                 elif "rawTokenAmount" in t:
#                     r = t["rawTokenAmount"] or {}
#                     try:
#                         amount = float(r.get("tokenAmount", 0)) / (10 ** int(r.get("decimals", 0)))
#                     except Exception:
#                         amount = 0.0

#                 if (
#                     from_wallet
#                     and to_wallet
#                     and from_wallet != to_wallet
#                     and amount > 0
#                 ):
#                     funding_events.append(
#                         {
#                             "parent": from_wallet,
#                             "child": to_wallet,
#                             "mint": SOL_MINT,
#                             "amount": amount,
#                             "timestamp": ts,
#                             "signature": txn.get("signature"),
#                         }
#                     )

#         # Collect swap events per wallet so we can see if children swapped later
#         logger.info("Extracting swap events from transactions...")
#         swap_events: Dict[str, Dict[str, Any]] = {}

#         for txn in transactions:
#             if (txn.get("type") or "").upper() != "SWAP":
#                 continue

#             ts = datetime.fromtimestamp(txn.get("timestamp", 0) or 0)
#             fee_payer = txn.get("feePayer")
#             events = (txn.get("events") or {}).get("swap") or {}

#             if not fee_payer:
#                 continue

#             # Inputs the fee payer provided into the swap
#             input_mints: List[str] = []
#             input_amounts: List[float] = []

#             for token_input in events.get("tokenInputs", []) or []:
#                 if token_input.get("userAccount") == fee_payer:
#                     input_mints.append(token_input.get("mint"))
#                     raw = token_input.get("rawTokenAmount") or {}
#                     try:
#                         amt = float(raw.get("tokenAmount", 0)) / (10 ** int(raw.get("decimals", 0)))
#                     except Exception:
#                         amt = 0.0
#                     input_amounts.append(amt)

#             # Outputs that landed back to the fee payer
#             output_mints: List[str] = []
#             for inner in events.get("innerSwaps", []) or []:
#                 for out in inner.get("tokenOutputs", []) or []:
#                     if out.get("toUserAccount") == fee_payer:
#                         output_mints.append(out.get("mint"))

#             swap_events[fee_payer] = {
#                 "timestamp": ts,
#                 "input_mints": input_mints,
#                 "output_mints": output_mints,
#                 "input_amounts": input_amounts,
#                 "signature": txn.get("signature"),
#             }

#         # Detect clusters
#         logger.info("Detecting funding clusters...")
#         clusters: List[Dict[str, Any]] = []
#         parent_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

#         for ev in funding_events:
#             parent_groups[ev["parent"]].append(ev)

#         for parent, parent_events in parent_groups.items():
#             parent_events.sort(key=lambda x: x["timestamp"])
#             for i in range(len(parent_events)):
#                 window_start = parent_events[i]["timestamp"]
#                 window_end = window_start + timedelta(minutes=funding_window_minutes)
#                 window_events = []
#                 for j in range(i, len(parent_events)):
#                     if parent_events[j]["timestamp"] <= window_end:
#                         window_events.append(parent_events[j])
#                     else:
#                         break

#                 unique_children = list({e["child"] for e in window_events})
#                 if len(unique_children) >= min_children:
#                     cluster = self._analyze_cluster(
#                         parent,
#                         window_events,
#                         unique_children,
#                         swap_events,
#                         window_start,
#                         window_end,
#                     )
#                     clusters.append(cluster)
#                     break  # move to next parent after first qualifying window

#         logger.info(f"Found {len(clusters)} wallet clusters")
#         return {
#             "detection_params": {
#                 "min_children": min_children,
#                 "funding_window_minutes": funding_window_minutes,
#                 "total_transactions_analyzed": len(transactions),
#             },
#             "summary": {
#                 "clusters_found": len(clusters),
#                 "total_parents": len(clusters),
#                 "total_children": sum(c["funding_stats"]["children_funded"] for c in clusters),
#                 "total_children_swapped": sum(c["swap_stats"]["children_swapped"] for c in clusters),
#             },
#             "clusters": clusters,
#         }

#     def _analyze_cluster(
#         self,
#         parent: str,
#         funding_events: List[Dict[str, Any]],
#         children: List[str],
#         swap_events: Dict[str, Dict[str, Any]],
#         window_start: datetime,
#         window_end: datetime,
#     ) -> Dict[str, Any]:
#         total_funding = sum(e["amount"] for e in funding_events)
#         funding_token = funding_events[0]["mint"]  # all funding we added is SOL/wSOL

#         children_data: List[Dict[str, Any]] = []
#         children_swapped = 0
#         total_swap_amount = 0.0
#         target_tokens = set()

#         for child in children:
#             child_funding = sum(e["amount"] for e in funding_events if e["child"] == child)
#             info = {
#                 "wallet": child,
#                 "funded_amount": round(child_funding, 9),
#                 "swap_status": "pending",
#                 "swap_amount": 0.0,
#                 "swap_time": None,
#                 "target_tokens": [],
#             }

#             if child in swap_events:
#                 swap = swap_events[child]
#                 if funding_token in swap.get("input_mints", []):
#                     info["swap_status"] = "completed"
#                     # find amount of funded token used
#                     for i, m in enumerate(swap["input_mints"]):
#                         if m == funding_token and i < len(swap["input_amounts"]):
#                             amt = float(swap["input_amounts"][i])
#                             info["swap_amount"] = amt
#                             total_swap_amount += amt
#                             break
#                     info["swap_time"] = swap["timestamp"].isoformat()
#                     info["target_tokens"] = swap.get("output_mints", [])
#                     children_swapped += 1
#                     target_tokens.update(info["target_tokens"])

#             children_data.append(info)

#         cluster_type = "BUY_CLUSTER" if funding_token in BUYING_POWER_TOKENS else "SELL_CLUSTER"

#         return {
#             "cluster_id": f"{parent}_{int(window_start.timestamp())}",
#             "parent_wallet": parent,
#             "formation_time": window_start.isoformat(),
#             "formation_window": f"{window_start.isoformat()} - {window_end.isoformat()}",
#             "cluster_type": cluster_type,
#             "funding_stats": {
#                 "children_funded": len(children),
#                 "total_amount_sent": round(total_funding, 9),
#                 "funding_token": funding_token,
#                 "funding_token_symbol": self._get_token_symbol(funding_token),
#             },
#             "swap_stats": {
#                 "children_swapped": children_swapped,
#                 "children_pending": len(children) - children_swapped,
#                 "total_amount_swapped": round(total_swap_amount, 9),
#                 "swap_completion_rate": f"{(children_swapped / len(children) * 100):.1f}%",
#                 "target_tokens": list(target_tokens),
#                 "coordinated_target": len(target_tokens) == 1,
#             },
#             "children": children_data,
#         }

#     def _get_token_symbol(self, mint: str) -> str:
#         token_symb_





# code 2 Sohail here

# app/services/helius_service.py

# from __future__ import annotations

# import logging
# from collections import defaultdict
# from datetime import datetime, timedelta
# from typing import Any, Dict, List, Optional

# import httpx

# from app.core.config import settings

# # -----------------------------
# # Constants / simple helpers
# # -----------------------------

# # Native SOL mint (Helius uses this symbolic mint for SOL)
# SOL_MINT = "So11111111111111111111111111111111111111112"

# # Common stablecoins (buying power)
# STABLECOIN_MINTS = {
#     "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
#     "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
#     "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",  # USDC (Circle)
#     "A9mUU4qviSctJVPJdBJWkb28deg915LYJKrzQ19ji3FM",  # USTv2
#     "Gz7VkD4MacbEB6yC5XD3HcumEiYx2EtDYYrfikGsvopG",  # wsUSDC
# }

# # Tokens that represent "buying power" (SOL + stablecoins)
# BUYING_POWER_TOKENS = {SOL_MINT} | STABLECOIN_MINTS

# # Log setup
# logger = logging.getLogger(__name__)
# if not logger.handlers:
#     logging.basicConfig(level=logging.INFO)


# def _to_float_token_amount(raw: Dict[str, Any]) -> float:
#     """Convert Helius rawTokenAmount to float SOL/token units."""
#     if not isinstance(raw, dict):
#         return 0.0
#     amt = raw.get("tokenAmount")
#     dec = raw.get("decimals", 0) or 0
#     # tokenAmount might already be human units; prefer exact division if it's raw integer
#     try:
#         # If it's a string int, we consider it raw base units
#         if isinstance(amt, str) and amt.isdigit():
#             return float(int(amt)) / (10 ** int(dec))
#         return float(amt or 0)
#     except Exception:
#         return 0.0


# # -----------------------------
# # Service
# # -----------------------------

# class HeliusService:
#     def __init__(self) -> None:
#         self.api_key: str = settings.HELIUS_API_KEY
#         self.base_url: str = settings.HELIUS_BASE_URL.rstrip("/")
#         # Optional override like: https://api.helius.xyz/v0/addresses/{address}/transactions?api-key={api_key}
#         self.url_template: Optional[str] = getattr(settings, "HELIUS_TRANSACTIONS_URL", None)

#     async def get_raw_transactions(
#         self, wallet_address: str, limit: int | None = None
#     ) -> List[Dict[str, Any]]:
#         """
#         Fetch parsed transactions for a wallet.

#         NOTE: `limit` is accepted for compatibility with the endpoint signature,
#         but **not forwarded** to Helius since that endpoint rejects unknown query params.
#         """
#         if self.url_template:
#             url = self.url_template.format(address=wallet_address, api_key=self.api_key)
#         else:
#             # Fallback default
#             url = f"{self.base_url}/addresses/{wallet_address}/transactions?api-key={self.api_key}"

#         try:
#             async with httpx.AsyncClient(timeout=30) as client:
#                 logger.info(f"Helius GET {url}")
#                 resp = await client.get(url)
#                 resp.raise_for_status()
#                 data = resp.json()
#                 if isinstance(data, dict) and "result" in data:
#                     return data["result"] or []
#                 return data if isinstance(data, list) else []
#         except httpx.HTTPStatusError as http_err:
#             logger.error(
#                 f"HTTP error from Helius: {http_err.response.status_code} - {http_err.response.text}"
#             )
#             raise
#         except Exception as e:
#             logger.error(f"Failed to fetch transactions: {e}")
#             raise

#     # -----------------------------
#     # Cluster detection
#     # -----------------------------

#     def detect_wallet_clusters(
#         self,
#         transactions: List[Dict[str, Any]],
#         min_children: int = 5,
#         funding_window_minutes: int = 5,
#     ) -> Dict[str, Any]:
#         """
#         Detect clusters where a parent wallet funds multiple child wallets
#         within a short window. Filters out Jupiter/AMM swap noise.
#         """
#         logger.info("Extracting funding events from transactions...")

#         funding_events: List[Dict[str, Any]] = []

#         for txn in transactions:
#             # Ignore router/pool noise for clustering
#             if (txn.get("type") == "SWAP") or (txn.get("source") == "JUPITER"):
#                 continue

#             ts = datetime.fromtimestamp(txn.get("timestamp", 0) or 0)

#             # Only consider user-to-user movements in tokenTransfers (Helius surfaces these)
#             for tr in txn.get("tokenTransfers", []):
#                 from_wallet = tr.get("fromUserAccount")
#                 to_wallet = tr.get("toUserAccount")
#                 if not from_wallet or not to_wallet or from_wallet == to_wallet:
#                     continue

#                 mint = tr.get("mint")
#                 # Prefer rawTokenAmount when present
#                 raw = tr.get("rawTokenAmount")
#                 amount = _to_float_token_amount(raw) if raw else float(tr.get("tokenAmount", 0) or 0)

#                 # Positive movement from parent -> child
#                 if amount > 0:
#                     funding_events.append(
#                         {
#                             "parent": from_wallet,
#                             "child": to_wallet,
#                             "mint": mint,
#                             "amount": amount,
#                             "timestamp": ts,
#                             "signature": txn.get("signature"),
#                         }
#                     )

#         logger.info("Extracting swap events from transactions...")
#         swap_events: Dict[str, Dict[str, Any]] = {}

#         for txn in transactions:
#             if txn.get("type") != "SWAP":
#                 continue

#             ts = datetime.fromtimestamp(txn.get("timestamp", 0) or 0)
#             fee_payer = txn.get("feePayer")
#             swap_data = txn.get("events", {}).get("swap", {})

#             if not fee_payer or not swap_data:
#                 continue

#             # Gather inputs the user actually provided
#             input_mints: List[str] = []
#             input_amounts: List[float] = []
#             for t_in in swap_data.get("tokenInputs", []):
#                 if t_in.get("userAccount") == fee_payer:
#                     input_mints.append(t_in.get("mint"))
#                     input_amounts.append(_to_float_token_amount(t_in.get("rawTokenAmount", {})))

#             # Tokens the user received
#             output_mints: List[str] = []
#             for inner in swap_data.get("innerSwaps", []):
#                 for t_out in inner.get("tokenOutputs", []):
#                     if t_out.get("toUserAccount") == fee_payer:
#                         output_mints.append(t_out.get("mint"))

#             swap_events[fee_payer] = {
#                 "timestamp": ts,
#                 "input_mints": input_mints,
#                 "output_mints": output_mints,
#                 "input_amounts": input_amounts,
#                 "signature": txn.get("signature"),
#             }

#         logger.info("Detecting funding clusters...")
#         clusters: List[Dict[str, Any]] = []

#         parent_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
#         for e in funding_events:
#             parent_groups[e["parent"]].append(e)

#         for parent, events in parent_groups.items():
#             events.sort(key=lambda x: x["timestamp"])

#             # Sliding window over parent events
#             for i in range(len(events)):
#                 win_start = events[i]["timestamp"]
#                 win_end = win_start + timedelta(minutes=funding_window_minutes)

#                 window: List[Dict[str, Any]] = []
#                 for j in range(i, len(events)):
#                     if events[j]["timestamp"] <= win_end:
#                         window.append(events[j])
#                     else:
#                         break

#                 unique_children = list({e["child"] for e in window})
#                 if len(unique_children) >= min_children:
#                     cluster = self._analyze_cluster(
#                         parent=parent,
#                         funding_events=window,
#                         children=unique_children,
#                         swap_events=swap_events,
#                         window_start=win_start,
#                         window_end=win_end,
#                     )
#                     clusters.append(cluster)
#                     break  # move to the next parent

#         logger.info(f"Found {len(clusters)} wallet clusters")

#         return {
#             "detection_params": {
#                 "min_children": min_children,
#                 "funding_window_minutes": funding_window_minutes,
#                 "total_transactions_analyzed": len(transactions),
#             },
#             "summary": {
#                 "clusters_found": len(clusters),
#                 "total_parents": len(clusters),
#                 "total_children": sum(c["funding_stats"]["children_funded"] for c in clusters),
#                 "total_children_swapped": sum(c["swap_stats"]["children_swapped"] for c in clusters),
#             },
#             "clusters": clusters,
#         }

#     # -----------------------------
#     # Internals
#     # -----------------------------

#     def _analyze_cluster(
#         self,
#         parent: str,
#         funding_events: List[Dict[str, Any]],
#         children: List[str],
#         swap_events: Dict[str, Dict[str, Any]],
#         window_start: datetime,
#         window_end: datetime,
#     ) -> Dict[str, Any]:
#         """Compute stats for a detected cluster."""
#         total_funding = sum(e["amount"] for e in funding_events)
#         # Use the most-common funding mint in the window
#         fund_mint_counts: Dict[str, int] = defaultdict(int)
#         for e in funding_events:
#             fund_mint_counts[e["mint"]] += 1
#         funding_token = max(fund_mint_counts, key=fund_mint_counts.get)

#         children_data: List[Dict[str, Any]] = []
#         children_swapped = 0
#         total_swap_amount = 0.0
#         target_tokens = set()

#         for child in children:
#             child_funds = [e for e in funding_events if e["child"] == child]
#             child_funded_amt = sum(e["amount"] for e in child_funds)

#             info = {
#                 "wallet": child,
#                 "funded_amount": round(child_funded_amt, 6),
#                 "swap_status": "pending",
#                 "swap_amount": 0.0,
#                 "swap_time": None,
#                 "target_tokens": [],
#             }

#             if child in swap_events:
#                 sw = swap_events[child]
#                 if funding_token in (sw.get("input_mints") or []):
#                     info["swap_status"] = "completed"

#                     # Sum the amount of the funding token the child used in the swap
#                     used = 0.0
#                     for mint, amt in zip(sw.get("input_mints", []), sw.get("input_amounts", [])):
#                         if mint == funding_token:
#                             used += float(amt or 0)
#                     info["swap_amount"] = round(used, 6)
#                     total_swap_amount += used

#                     info["swap_time"] = sw.get("timestamp").isoformat() if sw.get("timestamp") else None
#                     outs = sw.get("output_mints") or []
#                     info["target_tokens"] = outs
#                     target_tokens.update(outs)
#                     children_swapped += 1

#             children_data.append(info)

#         cluster_type = "BUY_CLUSTER" if funding_token in BUYING_POWER_TOKENS else "SELL_CLUSTER"

#         return {
#             "cluster_id": f"{parent}_{int(window_start.timestamp())}",
#             "parent_wallet": parent,
#             "formation_time": window_start.isoformat(),
#             "formation_window": f"{window_start.isoformat()} - {window_end.isoformat()}",
#             "cluster_type": cluster_type,
#             "funding_stats": {
#                 "children_funded": len(children),
#                 "total_amount_sent": round(total_funding, 6),
#                 "funding_token": funding_token,
#                 "funding_token_symbol": self._get_token_symbol(funding_token),
#             },
#             "swap_stats": {
#                 "children_swapped": children_swapped,
#                 "children_pending": len(children) - children_swapped,
#                 "total_amount_swapped": round(total_swap_amount, 6),
#                 "swap_completion_rate": f"{(children_swapped / len(children) * 100):.1f}%",
#                 "target_tokens": list(target_tokens),
#                 "coordinated_target": len(target_tokens) == 1,
#             },
#             "children": children_data,
#         }

#     def _get_token_symbol(self, mint: str) -> str:
#         """Minimal mint→symbol map."""
#         token_symbols = {
#             SOL_MINT: "SOL",
#             "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
#             "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
#             "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU": "USDC",
#             "A9mUU4qviSctJVPJdBJWkb28deg915LYJKrzQ19ji3FM": "USTv2",
#             "Gz7VkD4MacbEB6yC5XD3HcumEiYx2EtDYYrfikGsvopG": "wsUSDC",
#         }
#         return token_symbols.get(mint, "TOKEN")











# code 3 Sohail 


# app/services/helius_service.py
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

import httpx

from app.core.config import settings


# === Constants ===
SOL_MINT = "So11111111111111111111111111111111111111112"

# Common stablecoins on Solana
STABLECOIN_MINTS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",   # USDT
    "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",   # USDC (Circle)
    "A9mUU4qviSctJVPJdBJWkb28deg915LYJKrzQ19ji3FM",   # USTv2 (legacy)
    "Gz7VkD4MacbEB6yC5XD3HcumEiYx2EtDYYrfikGsvopG",   # wsUSDC
}

# Tokens that represent "buying power"
BUYING_POWER_TOKENS = {SOL_MINT} | STABLECOIN_MINTS

# Logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class HeliusService:
    def __init__(self) -> None:
        self.api_key = settings.HELIUS_API_KEY
        self.base_url = settings.HELIUS_BASE_URL

    # ---------- Helius fetch ----------
    async def get_raw_transactions(
        self, wallet_address: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch parsed transactions for a wallet via Helius.
        Returns the list Helius provides (already decoded).
        """
        url = f"{self.base_url}/addresses/{wallet_address}/transactions"
        params = {"api-key": self.api_key, "limit": limit}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                logger.info("HTTP Request: GET %s", url)
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                # Some responses may be wrapped in {"result": [...]}
                if isinstance(data, dict) and "result" in data:
                    data = data["result"]
                logger.info(
                    "Fetched %s transactions for %s", len(data), wallet_address
                )
                return data
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error: %s - %s", e.response.status_code, e.response.text
            )
            raise
        except Exception as e:
            logger.error("Failed to fetch transactions: %s", e)
            raise

    # ---------- Cluster detection ----------
    def detect_wallet_clusters(
        self,
        transactions: List[Dict[str, Any]],
        min_children: int = 5,
        funding_window_minutes: int = 5,
    ) -> Dict[str, Any]:
        """
        Detect clusters where a parent wallet funds multiple distinct child
        wallets within a short time window. Filters out swaps, airdrops, and mints
        as *funding* sources and counts only SOL + stablecoins as buying power.
        """

        # --- Step 1: Extract funding events (SOL + stablecoins only) ---
        logger.info("Extracting funding events from transactions...")
        funding_events: List[Dict[str, Any]] = []

        for txn in transactions:
            ts = datetime.fromtimestamp(txn.get("timestamp", 0))

            # Skip obvious non-funding sources for our purpose
            tx_type = (txn.get("type") or "").upper()
            tx_source = (txn.get("source") or "").upper()
            if tx_type in {"SWAP", "MINT", "AIRDROP"} or tx_source == "JUPITER":
                continue

            # 1) Native SOL transfers (lamports)
            for nt in txn.get("nativeTransfers", []) or []:
                from_w = nt.get("fromUserAccount")
                to_w = nt.get("toUserAccount")
                raw_amt = nt.get("amount", 0)

                # Helius usually returns lamports; be robust if it's already SOL
                try:
                    val = float(raw_amt)
                except Exception:
                    val = 0.0

                # Heuristic: if it's "big", treat as lamports and convert
                amount_sol = val / 1_000_000_000 if val > 1e6 else val

                if from_w and to_w and from_w != to_w and amount_sol > 0:
                    funding_events.append(
                        {
                            "parent": from_w,
                            "child": to_w,
                            "mint": SOL_MINT,
                            "amount": amount_sol,
                            "timestamp": ts,
                            "signature": txn.get("signature"),
                        }
                    )

            # 2) SPL token transfers (stablecoins only)
            for tt in txn.get("tokenTransfers", []) or []:
                mint = tt.get("mint")
                if mint not in STABLECOIN_MINTS:
                    continue

                from_w = tt.get("fromUserAccount")
                to_w = tt.get("toUserAccount")

                # Prefer rawTokenAmount for precision
                amt = 0.0
                raw = tt.get("rawTokenAmount") or {}
                if "tokenAmount" in raw and "decimals" in raw:
                    try:
                        amt = float(raw["tokenAmount"]) / (10 ** int(raw["decimals"]))
                    except Exception:
                        amt = 0.0
                else:
                    # Fallback if already adjusted
                    try:
                        amt = float(tt.get("tokenAmount", 0))
                    except Exception:
                        amt = 0.0

                if from_w and to_w and from_w != to_w and amt > 0:
                    funding_events.append(
                        {
                            "parent": from_w,
                            "child": to_w,
                            "mint": mint,
                            "amount": amt,
                            "timestamp": ts,
                            "signature": txn.get("signature"),
                        }
                    )

        # --- Step 2: Extract swap usage by children (optional analytics) ---
        logger.info("Extracting swap events from transactions...")
        swap_events: Dict[str, Dict[str, Any]] = {}  # child wallet -> swap info
        for txn in transactions:
            if (txn.get("type") or "").upper() != "SWAP":
                continue

            ts = datetime.fromtimestamp(txn.get("timestamp", 0))
            fee_payer = txn.get("feePayer")
            events = txn.get("events") or {}
            swap_data = events.get("swap") or {}
            if not fee_payer:
                continue

            input_mints: List[str] = []
            input_amounts: List[float] = []
            for t_in in swap_data.get("tokenInputs", []) or []:
                if t_in.get("userAccount") != fee_payer:
                    continue
                rm = t_in.get("rawTokenAmount") or {}
                try:
                    amount = float(rm.get("tokenAmount", 0)) / (
                        10 ** int(rm.get("decimals", 0))
                    )
                except Exception:
                    amount = 0.0
                input_mints.append(t_in.get("mint"))
                input_amounts.append(amount)

            output_mints: List[str] = []
            for inner in swap_data.get("innerSwaps", []) or []:
                for t_out in inner.get("tokenOutputs", []) or []:
                    if t_out.get("toUserAccount") == fee_payer:
                        output_mints.append(t_out.get("mint"))

            if input_mints or output_mints:
                swap_events[fee_payer] = {
                    "timestamp": ts,
                    "input_mints": input_mints,
                    "output_mints": output_mints,
                    "input_amounts": input_amounts,
                    "signature": txn.get("signature"),
                }

        # --- Step 3: Group funding by parent and find windows with >= min_children ---
        logger.info("Detecting funding clusters...")
        clusters: List[Dict[str, Any]] = []
        parent_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for ev in funding_events:
            parent_groups[ev["parent"]].append(ev)

        for parent, evs in parent_groups.items():
            evs.sort(key=lambda e: e["timestamp"])
            n = len(evs)
            for i in range(n):
                win_start = evs[i]["timestamp"]
                win_end = win_start + timedelta(minutes=funding_window_minutes)
                window_evs: List[Dict[str, Any]] = []
                for j in range(i, n):
                    if evs[j]["timestamp"] <= win_end:
                        window_evs.append(evs[j])
                    else:
                        break

                unique_children = list({e["child"] for e in window_evs})
                if len(unique_children) >= min_children:
                    clusters.append(
                        self._analyze_cluster(
                            parent=parent,
                            funding_events=window_evs,
                            children=unique_children,
                            swap_events=swap_events,
                            window_start=win_start,
                            window_end=win_end,
                        )
                    )
                    # Move to next parent after finding the first qualifying burst
                    break

        logger.info("Found %s wallet clusters", len(clusters))

        return {
            "detection_params": {
                "min_children": min_children,
                "funding_window_minutes": funding_window_minutes,
                "total_transactions_analyzed": len(transactions),
            },
            "summary": {
                "clusters_found": len(clusters),
                "total_parents": len(clusters),
                "total_children": sum(
                    c["funding_stats"]["children_funded"] for c in clusters
                ),
                "total_children_swapped": sum(
                    c["swap_stats"]["children_swapped"] for c in clusters
                ),
            },
            "clusters": clusters,
        }

    # ---------- Helpers ----------
    def _analyze_cluster(
        self,
        parent: str,
        funding_events: List[Dict[str, Any]],
        children: List[str],
        swap_events: Dict[str, Dict[str, Any]],
        window_start: datetime,
        window_end: datetime,
    ) -> Dict[str, Any]:
        total_funding = sum(e["amount"] for e in funding_events)
        # Pick mint from first event for labeling (most bursts are homogeneous)
        funding_token = funding_events[0]["mint"] if funding_events else SOL_MINT

        children_data: List[Dict[str, Any]] = []
        children_swapped = 0
        total_swap_amount = 0.0
        target_tokens = set()

        for child in children:
            child_evs = [e for e in funding_events if e["child"] == child]
            child_funded_amt = sum(e["amount"] for e in child_evs)

            info = {
                "wallet": child,
                "funded_amount": child_funded_amt,
                "swap_status": "pending",
                "swap_amount": 0.0,
                "swap_time": None,
                "target_tokens": [],
            }

            sw = swap_events.get(child)
            if sw and funding_token in (sw.get("input_mints") or []):
                # Use the amount of the funded token that was input
                amt_used = 0.0
                for idx, mint in enumerate(sw.get("input_mints") or []):
                    if mint == funding_token and idx < len(sw.get("input_amounts") or []):
                        amt_used = float(sw["input_amounts"][idx])
                        break

                info.update(
                    {
                        "swap_status": "completed",
                        "swap_amount": amt_used,
                        "swap_time": sw["timestamp"].isoformat(),
                        "target_tokens": sw.get("output_mints") or [],
                    }
                )
                children_swapped += 1
                total_swap_amount += amt_used
                target_tokens.update(sw.get("output_mints") or [])

            children_data.append(info)

        cluster_type = (
            "BUY_CLUSTER" if funding_token in BUYING_POWER_TOKENS else "SELL_CLUSTER"
        )

        return {
            "cluster_id": f"{parent}_{int(window_start.timestamp())}",
            "parent_wallet": parent,
            "formation_time": window_start.isoformat(),
            "formation_window": f"{window_start.isoformat()} - {window_end.isoformat()}",
            "cluster_type": cluster_type,
            "funding_stats": {
                "children_funded": len(children),
                "total_amount_sent": round(total_funding, 6),
                "funding_token": funding_token,
                "funding_token_symbol": self._get_token_symbol(funding_token),
            },
            "swap_stats": {
                "children_swapped": children_swapped,
                "children_pending": len(children) - children_swapped,
                "total_amount_swapped": round(total_swap_amount, 6),
                "swap_completion_rate": (
                    f"{(children_swapped / len(children) * 100):.1f}%"
                    if children
                    else "0.0%"
                ),
                "target_tokens": list(target_tokens),
                "coordinated_target": len(target_tokens) == 1,
            },
            "children": children_data,
        }

    def _get_token_symbol(self, mint: str) -> str:
        """Minimal mint->symbol map."""
        token_symbols = {
            SOL_MINT: "SOL",
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
            "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU": "USDC",
            "A9mUU4qviSctJVPJdBJWkb28deg915LYJKrzQ19ji3FM": "USTv2",
            "Gz7VkD4MacbEB6yC5XD3HcumEiYx2EtDYYrfikGsvopG": "wsUSDC",
        }
        return token_symbols.get(mint, "TOKEN")
