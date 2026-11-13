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

export default function Phase11AEVacuumSelection() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Vacuum selection is a topic, not a law</H1>
        <Text tone="secondary">
          Phase 11AE records that T09 was chosen as the next topic. It does
          not invent a vacuum-selection principle. Source:
          phase11ae-vacuum-selection-v1 · HUMAN-VACUUM-SELECTION-AUTHORIZATION-v1
          · frozen 4C c26df583… · 2026-09-25.
        </Text>
        <Row gap={8} wrap>
          <Pill tone="warning" active>
            PRINCIPLE_UNSPECIFIED
          </Pill>
          <Pill active>TOPIC ONLY</Pill>
          <Pill tone="neutral" active>
            PHASE_11AE_STOPPED
          </Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="Selecting a vacuum is not itself a physical law">
        HUMAN CHOOSES TOPIC, then HUMAN SPECIFIES EXACT PRINCIPLE, then HUMAN
        AUTHORIZES PRINCIPLE, then MACHINE AUDITS CONSEQUENCES. Category
        phrases such as minimize the potential or choose the stable vacuum
        are not sufficient authorization.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value="UNSPECIFIED" label="mathematical statement" />
        <Stat value="NOT_FOUND" label="vacuum selection" />
        <Stat value="NONE" label="parameter reduction" />
        <Stat value="NOT_FOUND" label="PFR / modulus stabilization" />
      </Grid>

      <H2>What was refused</H2>
      <Table
        headers={["attempt", "result"]}
        rows={[
          ["missing authorization", "NOT_AUTHORIZED / STOP"],
          ["topic name without exact statement", "PRINCIPLE_UNSPECIFIED / STOP"],
          ["machine-proposed global minimum", "POST_HOC_PRINCIPLE_SELECTION"],
          ["auto-compare reference examples", "blocked"],
          ["stationarity as selection", "blocked"],
          ["local stability as global minimum", "blocked"],
          ["vacuum selection as modulus stabilization", "blocked"],
        ]}
        striped
        rowTone={[
          "danger",
          "warning",
          "danger",
          "danger",
          "warning",
          "warning",
          "warning",
        ]}
      />

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Existing 11P structure, unused as a law</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                Stationary points and local Hessian cases remain REFERENCE_ONLY.
                Stationarity is not vacuum selection.
              </Text>
              <Text>
                A later exact principle must do the selection work explicitly.
                It must not silently become mediation or modulus stabilization.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>What the next authorization must contain</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                One exact mathematical statement: domain, variables, assumptions,
                admissible vacua, whether uniqueness is required, whether
                metastable vacua are allowed, and whether selection is local or
                global.
              </Text>
              <Text>
                Reference examples such as global minimum or local stability
                remain non-operational until a human names exactly one of them
                with full scope.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Callout tone="neutral" title="Documentary comparison only">
        Previous state: VACUUM_SELECTION = NOT_FOUND. Current phase:
        VACUUM_SELECTION_PRINCIPLE = EXPLICIT NEW PHYSICAL INPUT topic only.
        No ranking of alternative principles.
      </Callout>

      <Divider />
      <Text tone="secondary">
        11P–11AD hashes unchanged. Frozen 4C unchanged. No experimental input.
        PHASE_11AE_STOPPED = TRUE. T09 still requires an exact principle.
      </Text>
    </Stack>
  );
}
