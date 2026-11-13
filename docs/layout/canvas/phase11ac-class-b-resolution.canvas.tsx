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

export default function Phase11ACClassBResolution() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>CLASS-B resolution with existing modules</H1>
        <Text tone="secondary">
          Phase 11AC re-runs T04 and T05 only. No new physics, no new
          assumption, no new parameter. Source: phase11ac-class-b-resolution-v1
          · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>T04 EXECUTED</Pill>
          <Pill active>T05 EXECUTED</Pill>
          <Pill tone="warning" active>
            BOTH REMAIN PARTIAL
          </Pill>
          <Pill tone="neutral" active>
            PHASE_11AC_STOPPED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Execution is not an upgrade">
        Existing 11Y identities and stored P5J/P5K summaries were re-run.
        The 11Y A-map was applied to the already present 11S Yukawa-from-W
        structure. Missing Yukawa betas and REFERENCE_ONLY gauge RG keep both
        items PARTIAL.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="PARTIAL" label="T04 finite-order RG" />
        <Stat value="PARTIAL" label="T05 anomaly A-map" />
        <Stat value="0" label="new parameters / PFRs" />
        <Stat value="NOT_DERIVED" label="mediation selection" />
      </Grid>

      <H2>Required resolution table</H2>
      <Table
        headers={["item", "previous", "execution", "result", "new status", "new input?", "new parameter?"]}
        rows={[
          [
            "T04 finite-order RG",
            "PARTIAL",
            "EXECUTED",
            "identities hold; coverage incomplete",
            "PARTIAL",
            "NO",
            "NO",
          ],
          [
            "T05 anomaly A-map",
            "PARTIAL",
            "EXECUTED",
            "structural map holds; beta_y absent",
            "PARTIAL",
            "NO",
            "NO",
          ],
        ]}
        striped
        rowTone={["warning", "warning"]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>T04 missing coverage</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>P5J/P5K remain REFERENCE_ONLY for anomaly-mediation soft terms.</Text>
              <Text>Scheme factor c_scheme remains free.</Text>
              <Text>Yukawa betas are absent from the stored finite-order RG.</Text>
              <Text>All-orders RG is outside the permitted re-run.</Text>
              <Text>Finite order actually tested: one-loop (P5J) and two-loop (P5K) gauge RG.</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>T05 missing coverage</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>Cubic W-family Yukawa structure exists in 11S.</Text>
              <Text>No certified Yukawa beta_y exists.</Text>
              <Text>Grammar Yukawa sector is absent.</Text>
              <Text>A_y = c_scheme * beta_y * F_phi is not a PFR.</Text>
              <Text>F_phi remains independent of F_X and F_T.</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H2>What was not executed</H2>
      <Table
        headers={["class", "items", "status after 11AC"]}
        rows={[
          ["C", "T06–T08 identifications / universal f_a", "NOT_ACTIVATED"],
          ["D", "T09–T14 vacuum, SUGRA, UV, mixed mediation", "NOT_ACTIVATED"],
          ["E", "T15–T17 uniqueness, all-orders, experiment", "OPEN"],
        ]}
        striped
      />

      <Callout tone="neutral" title="Smallest legitimate next action">
        Do not execute CLASS C/D/E. Record T04/T05 as well-characterized
        PARTIAL dependencies. The next phase requires a separate authorization.
      </Callout>

      <Divider />
      <Text tone="secondary">
        11V–11AB hashes unchanged. Frozen 4C unchanged. NEW_PHYSICAL_INPUT_STATUS
        = FALSE. NEW_ASSUMPTION_STATUS = FALSE. PHASE_11AC_STOPPED = TRUE.
      </Text>
    </Stack>
  );
}
