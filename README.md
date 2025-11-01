# Noonlight for HomeAssistant (Self-Hosted Fork)

This is a modified version of the [Noonlight](https://noonlight.com) integration for HomeAssistant that connects directly to the Noonlight API for self-hosting.

[Noonlight](https://noonlight.com) connects your smart home to local emergency services to help keep you safe in case of a break-in, fire, or medical emergency.

### Noonlight service is currently only available in the United States & Canada

## Key Differences from Original

This fork removes the dependency on Konnected.io's intermediary service and connects directly to the Noonlight API:

- **Direct API Integration**: Uses Noonlight server token authentication instead of OAuth
- **Self-Hosted**: No dependency on Konnected.io's token service
- **Simplified Setup**: Requires only server token from Noonlight developer portal

## How it Works

Noonlight connects to emergency 9-1-1 services in all U.S. states and Canadian provinces. Backed by a UL-compliant alarm monitoring center and staffed 24/7 with live operators in the United States, Noonlight is standing by to send help to your home at a moment's notice.

When integrated with Home Assistant, a **Noonlight Alarm** switch will appear in your list of entities. When the Noonlight Alarm switch is turned _on_, this will send an emergency signal to Noonlight. You will be contacted by text and voice at the phone number you configure. If you confirm the emergency with the Noonlight operator, or if you're unable to respond, Noonlight will dispatch local emergency services to your home using the [longitude and latitude coordinates](https://www.home-assistant.io/docs/configuration/basic/#latitude) specified in your Home Assistant configuration or an address you specify in the Noonlight configuration.

Additionally, a new service will be exposed to Home Assistant: `noonlight.create_alarm`, which allows you to explicitly specify the type of emergency service required by the alarm: medical, fire, or police. By default, the switch entity assumes "police".

**False alarm?** No problem. Just tell the Noonlight operator your PIN when you are contacted and the alarm will be canceled. We're glad you're safe!

The _Noonlight Switch_ can be activated by any Home Assistant automation, just like any type of switch! [See examples below](#automation-examples).

## Initial set up

Setup requires a U.S. or Canada based mobile phone number and a Noonlight developer account.

1. Ensure that your [longitude and latitude coordinates](https://www.home-assistant.io/docs/configuration/basic/#latitude) are set accurately so that Noonlight knows where to send help.

2. Create a developer account at [developer.noonlight.com](https://developer.noonlight.com)

3. Obtain your server token from the developer dashboard

4. Install this integration in Home Assistant (see [Installation](#installation) below)

### Configuration

* `Server Token`: Your server token from the Noonlight developer portal

* `Phone Number`: U.S. mobile phone number for emergency contact

* `API Endpoint`: The Noonlight API endpoint (default: `https://api.noonlight.com/dispatch/v1`)

* `Location Mode`: Choose between Latitude/Longitude or Address

#### If Latitude/Longitude:

* `Latitude`: Will default to Latitude in Home Assistant

* `Longitude`: Will default to Longitude in Home Assistant

#### If Address:

* `Address`: Street address

* `Address 2`: Apartment, suite, etc. (optional)

* `City`: City/town name

* `State\Province`: Two-letter state or province abbreviation

* `Zip\Postal Code`: Zip code or Postal Code

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/noonlight2` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Noonlight" and configure with your server token and phone number


## Automation Examples

### Notify Noonlight when an intrusion alarm is triggered

This example is using the [Manual Alarm component](https://www.home-assistant.io/integrations/manual/)

```yaml
automation:
  - alias: 'Activate the Noonlight Alarm when the security system is triggered'
    trigger:
      - platform: state
        entity_id: 
          - alarm_control_panel.ha_alarm
        to: 'triggered'
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.noonlight_alarm
```

### Notify Noonlight when a smoke detector detects smoke

```yaml
automation:
  - alias: 'Activate the Noonlight Alarm when smoke is detected'
    trigger:
      - platform: state
        entity_id: 
          - binary_sensor.smoke_alarm
        to: 'on'        
    action:
      - service: noonlight.create_alarm
        data:
          service: fire
```

## Troubleshooting

### Common Issues

1. **"Failed to send an alarm to Noonlight"**
   - Verify your server token is correct
   - Check that your phone number is in U.S. format
   - Ensure Home Assistant has internet connectivity

2. **Integration not appearing**
   - Restart Home Assistant after installation
   - Check logs for any import errors
   - Verify the custom_components/noonlight folder structure

3. **Authentication errors**
   - Regenerate your server token from the Noonlight developer portal
   - Ensure the token has proper permissions

### Support

This is a community-maintained fork. For issues:
- Check the GitHub repository for similar issues
- Review Home Assistant logs for error details
- Test with the original Konnected.io integration to isolate issues

## Todo
- Add support for multiple contacts
- Add support for the "Cancel" function of the alarm
- Allow to clear the alarm status from client side (force turn off switch)

### Low priority todo
- Check phone number format and show error message if invalid (1NPANXXXXXX)
- Add support for the "Other" type of emergency
- Remove dependencies on the python noonlight package


## Warnings & Disclaimers

<p class='note warning'>
<b>Requires an Internet connection!</b> Home Assistant must have an active internet connection for this to work!
</p>

### NO GUARANTEE

**This integration is provided as-is without warranties of any kind. Using Noonlight with Home Assistant involves multiple service providers and potential points of failure, including (but not limited to) your internet service provider, 3rd party hosting services, and the Home Assistant software platform.**

**This is a community-maintained fork that bypasses Konnected.io's services. While this provides more control, it also means less testing and support than the original integration. Use at your own risks.**

Please read and understand the [Noonlight terms of use](https://noonlight.com/terms) and [Home Assistant terms of Service](https://www.home-assistant.io/tos/), each of which include important limitations of liability and indemnification provisions.
