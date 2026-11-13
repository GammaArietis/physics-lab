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

export default function Phase11WMediationAlternatives() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Mediation is not unique</H1>
        <Text tone="secondary">
          Phase 11W audits the unresolved mediation space without activating a
          second mechanism. Gravity mediation remains one explicit TEST
          EXTENSION, not a derived unique mechanism. Source:
          phase11w-mediation-alternatives-v1 · 11V HUMAN-SUSY-MEDIATION-AUTHORIZATION-v1
          unchanged · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill tone="warning" active>
            MEDIATION_SELECTION NOT_DERIVED
          </Pill>
          <Pill active>gravity EXISTING</Pill>
          <Pill tone="neutral" active>
            four alternatives NOT ACTIVATED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Not activated is not inconsistent">
        Supergravity does not imply gravity mediation. Existing beta functions
        do not activate anomaly mediation. Existing moduli are not mediation
        fields. U(1) does not imply gauge mediation. Fewer parameters are not
        a selection criterion.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="EXISTING" label="gravity branch (11V)" />
        <Stat value="NOT_ACTIVATED" label="gauge / anomaly / modulus / direct" />
        <Stat value="0" label="new parameters in 11W" />
        <Stat value="NOT_DERIVED" label="unique mediation" />
      </Grid>

      <H2>Structural comparison, not a ranking</H2>
      <Table
        headers={["mechanism", "new fields", "free scale", "status", "uniqueness"]}
        rows={[
          ["gravity", "hidden X (already in 11V)", "M INPUT", "EXISTING / PARTIAL", "NOT_DERIVED"],
          ["gauge", "messenger multiplets", "messenger mass", "NOT ACTIVATED", "NOT_DERIVED"],
          ["anomaly", "super-Weyl compensator", "not fixed by partial RG", "NOT ACTIVATED", "NOT_DERIVED"],
          ["modulus", "modulus-visible coupling", "modulus VEV / F_T", "NOT ACTIVATED", "NOT_DERIVED"],
          ["direct", "direct hidden-visible operators", "may be unsuppressed", "NOT ACTIVATED", "NOT_DERIVED"],
        ]}
        striped
        rowTone={["warning", "neutral", "neutral", "neutral", "neutral"]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>What the existing theory contains</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                11V TEST TERMS generate scalar and gaugino soft structures
                with unfixed coefficients. A/B terms remain PARTIAL. M is INPUT.
              </Text>
              <Text>
                11U old-minimal SUGRA is PARTIAL and does not rewrite frozen
                c0+c1 R. Supergravity is not gravity mediation.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>What a later test would need</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                HUMAN-SUSY-MEDIATION-GAUGE-AUTHORIZATION, or ANOMALY, MODULUS,
                or DIRECT, as a new independent phase.
              </Text>
              <Text>
                Messengers, anomaly-mediated operators, modulus-visible
                couplings, and direct hidden-visible operators were not added.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <Text tone="secondary">
        Hierarchy kept: one tested branch ≠ unique mechanism. NOT ACTIVATED ≠
        INCONSISTENT. Mediation ≠ vacuum selection ≠ UV completion. New PFR
        count: 0. 11V gravity branch unmodified.
      </Text>
    </Stack>
  );
}
