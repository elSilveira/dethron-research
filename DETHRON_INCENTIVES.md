# Incentives for maintaining the Dethron network

Date: 15/09/2026. A hypothesis the user added to the original vision. An assessment
document; no token, payment, contract or market was created.

## Intent

Pay the operators of gadgets, gateways and servers for useful processing, storage and
connectivity. An eventually tradable token could be one form of payment. The immediate
objective is to make operation viable and to reduce the voluntary abandonment of resources;
income distributed at world scale remains an aspiration, with no promise of yield or
adoption.

Payment may encourage availability, but it prevents neither physical failures, nor loss of
power, nor broken links, nor participants leaving. Recovery is still necessary. The economic
hypothesis does not automatically validate the technical hypothesis of survival with 5 % of
the nodes.

## Prior art and history

- [Golem](https://docs.golem.network/docs/golem/overview): providers offer computational
  resources to requestors in exchange for GLM. There are payment and transaction costs,
  described in [payments](https://docs.golem.network/docs/golem/payments).
- [Filecoin](https://docs.filecoin.io/basics/the-blockchain/proofs): uses proofs of
  replication and of storage over time. Those specific proofs are not generic proofs of
  processing or of message forwarding.
- The historical BitNet economy, `backup/BITNET_WEB3_ECONOMY/README.md`, already described a
  token, rewards and a bridge to blockchains. Claims of automatic appreciation, efficiency
  and liquidity in that document are not validated economic evidence.

Reading the historical README is not a complete audit of its implementation. No contracts,
bridges or old economic tests were executed at this stage. Paying for infrastructure with
tokens already has prior art; the novelty and viability of the Dethron policy require
validation of their own.

## A useful service first, the unit of payment separately

| Contracted service | Evidence to design | The incentive to avoid |
| --- | --- | --- |
| Processing | A verifiable result of the task within the deadline | Paying for busy CPU, for duration, or for a self-declared result |
| Storage | The contracted data recoverable over the period, with appropriate checks | Paying for invented bytes or unnecessary copies |
| Transport | Contracted forwarding and delivery, with receipts and a budget | Paying for fabricated traffic, loops, or the same obligation repeated |
| Availability and reserve | Contracted capacity, demonstrable on request | Paying for an online identity as though it were a service or an independent device |

A signature proves the authorship of a receipt, not necessarily useful work. Issuer,
provider and recipient may agree on receipts for fictitious work. Multiple identities
likewise do not prove multiple independent gadgets. Verification, dispute and abuse
detection have costs and limits to be measured. Necessary redundancy may be paid for,
provided it is explicitly contracted and accounted for; do not confuse a useful replica with
a duplicated charge.

## Where the value comes from

Choose a real source of funding: users of the service, organisations, subscriptions,
contracts or explicit subsidies. Issuing tokens demonstrates neither recurring revenue, nor
liquidity, nor anybody willing to buy them.

Measure separately:

```text
operator's result = revenue realisable from the service
                    - energy - connectivity - wear
                    - operations - charging and verification costs
```

Keep the network's accounts as well: user payments and subsidies, transfers, verification
and coordination expenses, and any future obligations. A hypothetical token quotation is not
realised revenue. Receiving a token, managing to sell it, and ending with a positive net
result are different events.

Initial funding may subsidise coverage before local demand exists, but it needs a defined
budget and duration. Measure what happens to the supply of nodes when that subsidy ends,
without presuming future appreciation.

Do not require every gadget to be profitable. Some resources may cost more to communicate
with, verify and pay than the work they can supply. Assess concentration too: large
operators may hold cost advantages, reducing the very diversity of providers the incentive
was meant to encourage.

## Compatibility with disconnection and partitions

A transport network may hold messages during a partition. A payment system cannot presume
that isolated spending records are globally consistent. Signing an offline promise does not
stop the same balance being promised to several operators.

Options to assess include pre-allocated credits with bounded exposure, provisional receipts
and later settlement. Document who bears the risk, when a charge is final, and how conflicts
are resolved. Do not promise unrestricted final payment on every island, or the absence of
double spending, without a demonstrated mechanism.

If settlement depends on a blockchain reachable only over the internet, record that
dependency. Delivery may continue offline while settlement waits. Creating a blockchain of
our own adds consensus and security; storage surviving with 5 % proves neither the security
nor the progress of that consensus.

## Proposed economic experiment

1. Choose a service and a requestor willing to use it; start with measured cost and usage
   receipts. Test credits are neither tradable nor real income.
2. Compare voluntary participation and paid service under an explicit budget, without mixing
   subsidy with organic demand. A financial pilot requires a later definition of
   participants, budget and specific authorisation.
3. Simulate attempts at duplicate charging, multiple identities, collusion, incorrect
   results, data loss and conflicting receipts after partitions.
4. Measure the usefulness delivered, the cost of verification, the operator's net result,
   the cost to the user, availability and concentration. Do not pay for the simulation.
5. Compare conventional charging, service credits and a transferable token. Choose a token
   only if it solves a need that outweighs its costs.

Continue if remuneration sustains a useful, verifiable and competitive service. Simplify or
abandon the token if it depends on speculative appreciation, rewards fictitious work, or
adds a dependency that violates the autonomy contract. The network can continue without a
currency of its own.

Status: a documented hypothesis; no new economic test executed. Resume at the
[validation plan](DETHRON_VALIDATION_PLAN.md), [autonomy](DETHRON_AUTONOMY_CONTRACT.md) and
[usefulness](DETHRON_UTILITY_VALIDATION.md).
