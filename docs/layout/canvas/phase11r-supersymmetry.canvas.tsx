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

export default function Phase11RSupersymmetry() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Supersymmetry as input</H1>
        <Text tone="secondary">
          Phase 11R adds 4D rigid N=1 supersymmetry as an explicit new
          physical input and tests structural consequences. It does not
          claim the existing project derived supersymmetry. Source:
          phase11r-supersymmetry-v1 · HUMAN-SUSY-AUTHORIZATION-v1 · frozen
          4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>NEW PHYSICAL INPUT</Pill>
          <Pill tone="warning" active>
            UNIQUE THEORY NOT DERIVED
          </Pill>
          <Pill active>TEST EXTENSION</Pill>
          <Pill active>supergravity absent</Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Input is not a prediction">
        Under the explicitly added SUSY input, additional structural
        constraints were derived. The existing project does not predict
        supersymmetry. Reduced parameter count is not a unique theory.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="ABSENT" label="coverage before" />
        <Stat value="PARTIAL" label="module after" />
        <Stat value="1" label="new PFR (given cubic W)" />
        <Stat value="NOT_DERIVED" label="unique theory" />
      </Grid>

      <H2>What the input adds</H2>
      <Table
        headers={["layer", "status", "note"]}
        rows={[
          ["4D rigid N=1 superalgebra", "VERIFIED", "INPUT; no central charges"],
          ["chiral + vector multiplets", "PARTIAL", "Pi, psi, F, lambda, D required"],
          ["on-shell DOF matching", "VERIFIED", "2+2 chiral; 2+2 vector"],
          ["off-shell closure", "PARTIAL", "auxiliaries identified; freeze not rewritten"],
          ["superpotential", "PARTIAL", "holomorphic family; not unique"],
          ["moduli", "VERIFIED", "present when W vanishes"],
          ["SUSY breaking", "ABSENT", "not activated"],
          ["supergravity", "ABSENT", "required only for a stronger claim"],
        ]}
        striped
        rowTone={[
          "success",
          "warning",
          "success",
          "warning",
          "warning",
          "success",
          "neutral",
          "neutral",
        ]}
      />

      <H2>Parameter movement</H2>
      <Table
        headers={["quantity", "before", "after SUSY"]}
        rows={[
          ["c0, c1", "FREE", "FREE"],
          ["lambda_a, lambda_b", "FREE", "FREE"],
          ["gauge coupling / normalization", "FREE", "FREE"],
          ["scalar / Yukawa / quartic", "independent", "related given W; W still free"],
          ["Fayet–Iliopoulos xi", "absent", "optional new U(1) parameter"],
        ]}
        striped
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Derived given the input</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                F = dW/dPhi. Yukawa from W second derivative. For cubic W
                the quartic-to-Yukawa-squared ratio is one over four.
              </Text>
              <Text>
                Real Phi does not fill a chiral multiplet. U(1) does not
                fill a vector multiplet without a gaugino and D.
              </Text>
              <Text>
                New parameters: 1 (optional xi). Reduced relations: 2.
                Remaining free function: holomorphic W.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Left open</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Unique superpotential, unique vacuum, unique gauge group.</Text>
              <Text>Anomaly cancellation as a model selector.</Text>
              <Text>Nonperturbative UV completion; 11Q stays PARTIAL.</Text>
              <Text>
                Local supersymmetry in dynamical gravity. That branch needs
                supergravity as a further input, which was not added.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: SUSY as input ≠ consequences of SUSY. Vacuum
        selection stays NOT_FOUND. UV completion stays NOT_FOUND. M6–M10,
        global gauge, and gravity–matter stay PARTIAL.
      </Text>
    </Stack>
  );
}
