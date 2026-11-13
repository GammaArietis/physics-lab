import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

export default function Phase11ABMediationSynthesis() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Mediation synthesis and PARTIAL triage</H1>
        <Text tone="secondary">
          Phase 11AB describes the five isolated mediation branches and
          classifies remaining PARTIAL / UNTESTED items. It does not select a
          mechanism, merge branches, or introduce new physics. Source:
          phase11ab-mediation-synthesis-v1 · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>SYNTHESIS + TRIAGE ONLY</Pill>
          <Pill tone="warning" active>
            SELECTION NOT_DERIVED
          </Pill>
          <Pill active>17 items classified</Pill>
          <Pill tone="neutral" active>
            PHASE_11AB_STOPPED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Two operations, not a preferred mechanism">
        Synthesis records the current isolated state. Triage assigns each
        remaining PARTIAL or UNTESTED item exactly one class A–E. Classification
        is not a VERIFIED upgrade. Shared soft-term type is not mechanism
        equivalence. Shared symbols are not shared origin.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="5" label="isolated branches preserved" />
        <Stat value="0" label="union of certified PFRs" />
        <Stat value="DISTINCT" label="all ten equivalence pairs" />
        <Stat value="NOT_DERIVED" label="mediation selection" />
      </Grid>

      <H2>Structural synthesis (descriptive only)</H2>
      <Table
        headers={[
          "property",
          "11V gravity",
          "11X gauge",
          "11Y anomaly",
          "11Z modulus",
          "11AA direct",
        ]}
        rows={[
          ["input status", "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED"],
          ["new parameters", "1", "2", "1", "2", "3"],
          ["reduced parameters", "0", "0", "0", "0", "0"],
          ["PFR", "0", "0", "0", "0", "0"],
          ["gaugino", "VERIFIED", "VERIFIED", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["scalar soft", "VERIFIED", "VERIFIED", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["A", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "UNTESTED"],
          ["B", "PARTIAL", "PARTIAL", "PARTIAL", "UNTESTED", "UNTESTED"],
          ["RG", "UNTESTED", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["R-symmetry", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["SUGRA", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["vacuum", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL", "PARTIAL"],
          ["moduli", "VERIFIED", "VERIFIED", "NOT_FOUND", "NOT_FOUND", "NOT_FOUND"],
          ["UV", "PARTIAL", "PARTIAL", "PARTIAL", "NOT_FOUND", "NOT_FOUND"],
          ["uniqueness", "NOT_DERIVED", "NOT_DERIVED", "NOT_DERIVED", "NOT_DERIVED", "NOT_DERIVED"],
        ]}
        striped
      />

      <Grid columns={3} gap={16}>
        <Card>
          <CardHeader>Common structures</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Explicit NEW PHYSICAL INPUT authorization.</Text>
              <Text>TEST EXTENSION, not a derived unique theory.</Text>
              <Text>Hidden or background F-term communication.</Text>
              <Text>No vacuum selection. No UV completion.</Text>
              <Text>c0 and c1 remain FREE. No experimental constants.</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Branch-specific structures</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>11V: M-suppressed hidden-visible operators.</Text>
              <Text>11X: messenger loops with M, y.</Text>
              <Text>11Y: compensator F_phi with RG maps.</Text>
              <Text>11Z: new T, f_a(T), Z_i.</Text>
              <Text>11AA: O_W and O_K with independent M_direct.</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Unresolved structures</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Mediation uniqueness and selection.</Text>
              <Text>Vacuum selection and modulus stabilization.</Text>
              <Text>Full quantum SUGRA and UV completion.</Text>
              <Text>A / B / FI completeness.</Text>
              <Text>All-orders RG.</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>PARTIAL triage (central output)</H2>
      <Table
        headers={["id", "component", "class", "relevance", "resolution"]}
        rows={[
          ["T01", "F_X / F_phi / F_T distinctness", "A", "CLOSURE_CRITICAL", "EXECUTED in 11AB"],
          ["T02", "PFR union across isolated branches", "A", "CLOSURE_CRITICAL", "EXECUTED; union 0"],
          ["T03", "descriptive parameter totals", "A", "LOCAL", "EXECUTED; not a score"],
          ["T04", "finite-order RG re-run", "B", "NON_BLOCKING", "AVAILABLE, not executed"],
          ["T05", "11Y A-map on existing Yukawas", "B", "DOWNSTREAM", "AVAILABLE, not executed"],
          ["T06", "identify F_X with F_phi", "C", "HIGH_DEPENDENCY", "NOT_ACTIVATED"],
          ["T07", "identify F_T with F_X or F_phi", "C", "HIGH_DEPENDENCY", "NOT_ACTIVATED"],
          ["T08", "universal f_a or fixed weights", "C", "LOCAL", "NOT_ACTIVATED"],
          ["T09", "vacuum selection principle", "D", "CLOSURE_CRITICAL", "NOT_ACTIVATED"],
          ["T10", "modulus stabilization", "D", "CLOSURE_CRITICAL", "NOT_ACTIVATED"],
          ["T11", "full quantum SUGRA", "D", "CLOSURE_CRITICAL", "NOT_ACTIVATED"],
          ["T12", "UV completion", "D", "CLOSURE_CRITICAL", "NOT_ACTIVATED"],
          ["T13", "extra A/B/FI operators", "D", "DOWNSTREAM", "NOT_ACTIVATED"],
          ["T14", "mixed mediation", "D", "HIGH_DEPENDENCY", "NOT_ACTIVATED"],
          ["T15", "uniqueness / selection theorem", "E", "CLOSURE_CRITICAL", "LEAVE_OPEN"],
          ["T16", "all-orders RG / nonperturbative UV", "E", "NON_BLOCKING", "LEAVE_OPEN"],
          ["T17", "experimental comparison", "E", "NON_BLOCKING", "LEAVE_OPEN"],
        ]}
        striped
        rowTone={[
          "success",
          "success",
          "success",
          "warning",
          "warning",
          "neutral",
          "neutral",
          "neutral",
          "danger",
          "danger",
          "danger",
          "danger",
          "danger",
          "danger",
          "neutral",
          "neutral",
          "neutral",
        ]}
      />

      <Grid columns={5} gap={12}>
        <Stat value="T01–T03" label="RESOLVE_NOW (A)" />
        <Stat value="T04–T05" label="existing modules (B)" />
        <Stat value="T06–T08" label="new assumption (C)" />
        <Stat value="T09–T14" label="new physical input (D)" />
        <Stat value="T15–T17" label="leave open (E)" />
      </Grid>

      <H2>Parameter synthesis (provenance preserved)</H2>
      <Table
        headers={["quantity", "branches", "independent across branches?", "constrained?"]}
        rows={[
          ["F_X", "11V, 11X, 11AA", "yes; shared symbol is not shared origin", "no"],
          ["F_phi", "11Y", "yes", "no"],
          ["F_T", "11Z", "yes", "no"],
          ["M", "11V, 11X", "yes; not identified", "no"],
          ["M_direct", "11AA", "yes; not messenger mass", "no"],
          ["y / c_W / c_K", "11X / 11AA / 11AA", "yes", "no"],
          ["f_a(T), Z_i", "11Z", "yes", "no"],
          ["W, K, g, xi", "all, independently", "yes", "no"],
          ["c0, c1", "all", "yes; FREE INPUT", "no"],
        ]}
        striped
      />

      <Callout tone="neutral" title="Next action is a map, not a score">
        CLASS A identities are already executed as 11AB tests and do not upgrade
        source branches. CLASS B remains RESOLUTION_AVAILABLE. CLASS C/D remain
        recorded, not activated. CLASS E remains open. Do not start mixed
        mediation, mediation selection, or a PARTIAL-resolution phase.
      </Callout>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: 11V ≠ 11X ≠ 11Y ≠ 11Z ≠ 11AA. F_X ≠ F_phi ≠ F_T.
        M_direct ≠ messenger mass. MEDIATION_SELECTION_STATUS = NOT_DERIVED.
        PHASE_11AB_STOPPED = TRUE. Branch hashes unchanged.
      </Text>
    </Stack>
  );
}
