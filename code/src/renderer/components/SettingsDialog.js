import { createMuiTheme } from "@material-ui/core";
import Switch from "@material-ui/core/Switch";
import ThemeProvider from "@material-ui/styles/ThemeProvider";
import * as React from "react";
import { useSettingsKey } from "../../web/settings";
import { dialogWrap } from "../utils/dialogWrap.js";

function SettingsDialog() {
  const theme = React.useMemo(
    () =>
      createMuiTheme({
        palette: {
          type: "dark",
        },
      }),
    []
  );

  const [autocomplete, setAutocomplete] = useSettingsKey("enableAutocomplete");

  return (
    <ThemeProvider theme={theme}>
      <form className="settingsDialogForm">
        <table>
          <thead>
            <tr>
              <th>Option</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <label htmlFor="autocomplete-control">
                  Enable editor autocomplete
                </label>
              </td>
              <td>
                <Switch
                  checked={autocomplete}
                  onChange={(e) => setAutocomplete(e.target.checked)}
                  color="secondary"
                  inputProps={{ id: "autocomplete-control" }}
                />
              </td>
            </tr>
          </tbody>
        </table>
      </form>
    </ThemeProvider>
  );
}

export default dialogWrap("Settings", SettingsDialog, "row");
