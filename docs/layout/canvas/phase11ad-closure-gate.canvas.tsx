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

export default function Phase11ADClosureGate() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Authorization boundary after CLASS-B exhaustion</H1>
        <Text tone="secondary">
          Phase 11AD is a closure gate only. It does not activate CLASS C or
          CLASS D, and it does not select a mediation mechanism. Source:
          phase11ad-closure-gate-v1 · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill active>GATE COMPLETE</Pill>
          <Pill tone="warning" active>
            NOTHING ACTIVATED
          </Pill>
          <Pill active>CLASS-B PATH EXHAUSTED</Pill>
          <Pill tone="neutral" active>
            PHASE_11AD_STOPPED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="The permitted no-new-input path is exhausted">
        At the present stage, the laboratory has exhausted the permitted
        no-new-input resolution path for the mediation branches. Any further
        closure of CLASS C or CLASS D items requires explicit authorization.
        CLASS E items remain outside the current scope.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="COMPLETE" label="closure gate" />
        <Stat value="NOT_AUTHORIZED" label="CLASS C and CLASS D" />
        <Stat value="OPEN" label="CLASS E scope" />
        <Stat value="NOT_DERIVED" label="mediation selection" />
      </Grid>

      <H2>Decision map</H2>
      <Table
        headers={["item", "decision", "class"]}
        rows={[
          ["T04", "CLOSED_AT_PERMITTED_SCOPE", "B"],
          ["T05", "CLOSED_AT_PERMITTED_SCOPE", "B"],
          ["T06 F_X = F_Phi", "REQUIRES_EXPLICIT_ASSUMPTION", "C"],
          ["T07 F_T identification", "REQUIRES_EXPLICIT_ASSUMPTION", "C"],
          ["T08 universal f_a / weights", "REQUIRES_EXPLICIT_ASSUMPTION", "C"],
          ["T09 vacuum principle", "REQUIRES_NEW_PHYSICAL_INPUT", "D"],
          ["T10 modulus stabilization", "REQUIRES_NEW_PHYSICAL_INPUT", "D"],
          ["T11 full quantum SUGRA", "REQUIRES_NEW_PHYSICAL_INPUT", "D"],
          ["T12 UV completion", "REQUIRES_NEW_PHYSICAL_INPUT", "D"],
          ["T13 extra A/B/FI operators", "REQUIRES_NEW_PHYSICAL_INPUT", "D"],
          ["T14 mixed mediation", "REQUIRES_NEW_PHYSICAL_INPUT", "D"],
          ["T15 uniqueness / selection", "OUT_OF_SCOPE", "E"],
          ["T16 all-orders / nonperturbative", "OUT_OF_SCOPE", "E"],
          ["T17 experimental comparison", "FORBIDDEN_IN_CURRENT_SCOPE", "E"],
        ]}
        striped
        rowTone={[
          "success",
          "success",
          "warning",
          "warning",
          "warning",
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

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>What a future authorization must name</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                A unique authorization object with authorization_id,
                physical_input, mathematical_statement, scope, parent_inputs,
                provenance, declaration_hash, and activated_phase.
              </Text>
              <Text>
                Allowed states are NOT_AUTHORIZED, AUTHORIZED, or FROZEN.
                Only AUTHORIZED or FROZEN may activate the named object.
              </Text>
              <Text>
                Generic continue or resolve remaining partials is not
                sufficient physical authorization.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>What 11AD refused</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>No CLASS C assumption was activated.</Text>
              <Text>No CLASS D physical input was activated.</Text>
              <Text>No mediation mechanism was selected.</Text>
              <Text>Silent language such as assume, take, identify, naturally, standard, or minimal cannot activate physics.</Text>
              <Text>Branches remain independent. Combined mediation needs its own authorization.</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Callout tone="neutral" title="Next-phase contract">
        11AD does not launch another phase. The next physical step begins only
        after a human decision authorizes one specific CLASS C assumption or
        one specific CLASS D physical input.
      </Callout>

      <Divider />
      <Text tone="secondary">
        11V–11AC hashes unchanged. Frozen 4C unchanged. NEW_PHYSICAL_INPUT_STATUS
        = FALSE. NEW_ASSUMPTION_STATUS = FALSE. PHASE_11AD_STOPPED = TRUE.
      </Text>
    </Stack>
  );
}
